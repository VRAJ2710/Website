const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");
const { execFile, spawn } = require("node:child_process");
const { EventEmitter } = require("node:events");
const { promisify } = require("node:util");
const nodeTest = require("node:test");
const { neon } = require("@neondatabase/serverless");

const applicationDatabaseUrl = process.env.DATABASE_URL;
const configuredTestDatabaseUrl = process.env.AUTH_TEST_DATABASE_URL;
const execFileAsync = promisify(execFile);
const signalProbe = process.env.AUTH_TEST_SIGNAL_PROBE === "1";
const test = signalProbe ? nodeTest.test.skip : nodeTest.test;
let databaseUrl = configuredTestDatabaseUrl;
let temporaryDatabaseName;

function databaseHost(value) {
  try {
    return new URL(value).hostname;
  } catch {
    return "";
  }
}

function assertIsolatedDatabase() {
  if (!databaseUrl) {
    throw new Error(
      "AUTH_TEST_DATABASE_URL is required unless a local PostgreSQL service is available; auth integration tests never fall back to DATABASE_URL"
    );
  }
  if (applicationDatabaseUrl && databaseUrl === applicationDatabaseUrl) {
    throw new Error(
      "AUTH_TEST_DATABASE_URL must be different from DATABASE_URL; refusing to run against the application database"
    );
  }
  if (!databaseHost(databaseUrl)) {
    throw new Error("AUTH_TEST_DATABASE_URL must be a valid database URL");
  }
}

async function prepareTestDatabase({
  run = execFileAsync,
  env = process.env,
  applicationUrl = applicationDatabaseUrl,
  configuredUrl = configuredTestDatabaseUrl,
} = {}) {
  if (configuredUrl) {
    databaseUrl = configuredUrl;
    assertIsolatedDatabase();
    return;
  }

  const host = env.PGHOST;
  const user = env.PGUSER || "postgres";
  if (!host) {
    throw new Error(
      "AUTH_TEST_DATABASE_URL is required when PGHOST is unavailable; refusing to run against the application database"
    );
  }

  temporaryDatabaseName = `dispatch_auth_test_${process.pid}_${Date.now()}`;
  try {
    await run("createdb", [
      "--host", host,
      ...(env.PGPORT ? ["--port", env.PGPORT] : []),
      "--username", user,
      temporaryDatabaseName,
    ]);

    const baseUrl = new URL(applicationUrl || "postgresql://localhost/postgres");
    baseUrl.hostname = host;
    baseUrl.username = user;
    baseUrl.password = "";
    baseUrl.pathname = `/${temporaryDatabaseName}`;
    databaseUrl = baseUrl.toString();
    assertIsolatedDatabase();
  } catch (error) {
    try {
      await removeTestDatabase({ run, env });
    } catch (cleanupError) {
      error.message = `${error.message}; cleanup failed: ${cleanupError.message}`;
    }
    throw new Error(`Unable to create the isolated auth test database: ${oneLine(error.stderr || error.message)}`);
  }
}

async function removeTestDatabase({ run = execFileAsync, env = process.env } = {}) {
  if (!temporaryDatabaseName) return;
  const name = temporaryDatabaseName;
  try {
    await run("dropdb", [
      "--if-exists",
      "--host", env.PGHOST,
      ...(env.PGPORT ? ["--port", env.PGPORT] : []),
      "--username", env.PGUSER || "postgres",
      name,
    ]);
    temporaryDatabaseName = undefined;
  } catch (error) {
    throw new Error(`Unable to remove the isolated auth test database: ${oneLine(error.stderr || error.message)}`);
  }
}

async function cleanupAccountFlow({ cleanup, remove = removeTestDatabase } = {}) {
  let accountError;
  try {
    await cleanup();
  } catch (error) {
    accountError = error;
  }

  try {
    await remove();
  } catch (cleanupError) {
    if (!accountError) throw cleanupError;
    accountError.message = `${accountError.message}; cleanup failed: ${cleanupError.message}`;
  }

  if (accountError) throw accountError;
}

function oneLine(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

async function freePort() {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const port = probe.address().port;
      probe.close(() => resolve(port));
    });
  });
}

async function waitForServer(baseUrl, child) {
  const deadline = Date.now() + 45_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`server exited during startup with code ${child.exitCode}`);
    try {
      const response = await fetch(`${baseUrl}/api/me`);
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error("timed out waiting for server startup");
}

function cookieFrom(response) {
  const header = response.headers.get("set-cookie") || "";
  const match = header.match(/dispatch_session=([^;]+)/);
  assert.ok(match, "expected a dispatch_session cookie");
  return `dispatch_session=${match[1]}`;
}

async function form(baseUrl, pathname, values, options = {}) {
  return fetch(`${baseUrl}${pathname}`, {
    method: "POST",
    redirect: "manual",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      ...(options.cookie ? { Cookie: options.cookie } : {}),
    },
    body: new URLSearchParams(values),
  });
}

function resetTokenFrom(html) {
  const match = html.match(/href="\/__auth\/reset\?token=([^"]+)"/);
  assert.ok(match, "expected a one-time reset link");
  return decodeURIComponent(match[1]);
}

function tokenHash(token) {
  return crypto.createHash("sha256").update(token).digest("hex");
}

async function startServer(port, { spawnProcess = spawn } = {}) {
  const child = spawnProcess(process.execPath, [path.join(__dirname, "..", "server.js")], {
    env: {
      ...process.env,
      NODE_ENV: "test",
      PORT: String(port),
      DATABASE_URL: databaseUrl,
      AUTH_TEST_DATABASE_URL: databaseUrl,
      APPLICATION_DATABASE_URL: applicationDatabaseUrl || "",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stderr = "";
  child.stderr.on("data", chunk => { stderr += chunk.toString(); });
  const baseUrl = `http://127.0.0.1:${port}`;
  try {
    await waitForServer(baseUrl, child);
  } catch (error) {
    child.kill("SIGKILL");
    throw new Error(`${error.message}\n${oneLine(stderr)}`);
  }
  return { child, baseUrl };
}

async function stopServer(child) {
  if (child.exitCode !== null) return;
  child.kill("SIGTERM");
  await new Promise(resolve => {
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      resolve();
    }, 5_000);
    child.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

if (signalProbe) {
  nodeTest.test("cleans up the temporary database on forced shutdown", async () => {
    const markerPath = process.env.AUTH_TEST_SIGNAL_MARKER;
    const env = { PGHOST: "127.0.0.1" };
    const run = async (command, args) => {
      fs.appendFileSync(markerPath, `${command} ${args.at(-1)}\n`);
      if (command === "dropdb" && process.env.AUTH_TEST_SIGNAL_CLEANUP_FAILURE === "1") {
        throw new Error("simulated dropdb failure");
      }
      if (command === "dropdb" && process.env.AUTH_TEST_SIGNAL_CLEANUP_DELAY_MS) {
        await new Promise(resolve => setTimeout(resolve, Number(process.env.AUTH_TEST_SIGNAL_CLEANUP_DELAY_MS)));
      }
    };
    let shutdownStarted = false;
    const onSignal = signal => {
      if (shutdownStarted) return;
      shutdownStarted = true;
      removeTestDatabase({ run, env })
        .then(() => fs.appendFileSync(markerPath, "cleanup complete\n"))
        .catch(error => fs.appendFileSync(markerPath, `cleanup failed: ${oneLine(error.message)}\n`))
        .finally(() => process.exit(signal === "SIGINT" ? 130 : 143));
    };

    process.on("SIGINT", onSignal);
    process.on("SIGTERM", onSignal);
    await prepareTestDatabase({
      run,
      env,
      applicationUrl: "postgresql://localhost/postgres",
      configuredUrl: undefined,
    });
    fs.appendFileSync(markerPath, "ready\n");
    process.stdout.write("ready\n");
    setInterval(() => {}, 1_000);
    await new Promise(() => {});
  });
}

test("persistent account, session, and one-time recovery flows", async t => {
  let sql;
  let email;
  let running;
  let cleanedUp = false;

  async function cleanup() {
    if (cleanedUp) return;
    cleanedUp = true;
    if (running) await stopServer(running.child);
    if (sql && email) await sql`DELETE FROM dispatch_users WHERE email=${email}`;
  }

  const onSignal = signal => {
    cleanupAccountFlow({ cleanup })
      .finally(() => process.exit(signal === "SIGINT" ? 130 : 143));
  };

  try {
    process.once("SIGINT", onSignal);
    process.once("SIGTERM", onSignal);
    await prepareTestDatabase();

    sql = neon(databaseUrl);
    const port = await freePort();
    email = `auth-test-${crypto.randomUUID()}@example.com`;
    const originalPassword = "Original-password-123";
    const recoveredPassword = "Recovered-password-456";
    running = await startServer(port);

    await t.test("restricts RSS fetching to approved feed identifiers", async () => {
      const rejected = await fetch(`${running.baseUrl}/api/rss-feed?url=http://127.0.0.1:5432/`);
      assert.equal(rejected.status, 400);
      assert.deepEqual(await rejected.json(), { error: "Unknown RSS feed." });
      const approved = await fetch(`${running.baseUrl}/api/rss-feed?feed=f0`);
      assert.equal(approved.status, 200);
      assert.match(approved.headers.get("content-type") || "", /application\/xml/);
    });

    await t.test("serves only public assets, never server source, configs, or .git", async () => {
      // Public assets must remain reachable.
      for (const asset of ["/", "/index.html", "/app.js", "/styles.css"]) {
        const ok = await fetch(`${running.baseUrl}${asset}`);
        assert.equal(ok.status, 200, `expected ${asset} to be served`);
      }
      // Server source, configuration, tests, scripts, dependencies and the git
      // repo must never be downloadable.
      for (const secret of [
        "/server.js",
        "/stripeClient.js",
        "/marketProxy.js",
        "/rssFeeds.js",
        "/package.json",
        "/package-lock.json",
        "/.replit",
        "/replit.md",
        "/.git/config",
        "/test/auth.integration.test.js",
        "/scripts/seed-stripe-products.js",
      ]) {
        const blocked = await fetch(`${running.baseUrl}${secret}`, { redirect: "manual" });
        assert.equal(blocked.status, 404, `expected ${secret} to be blocked, got ${blocked.status}`);
      }
    });

    await t.test("creates an account without exposing its password hash", async () => {
      const response = await form(running.baseUrl, "/__auth/subscribe", {
        email,
        password: originalPassword,
      });
      assert.equal(response.status, 302);
      assert.equal(response.headers.get("location"), "/?checkout=1");

      const cookie = cookieFrom(response);
      const me = await runningFetch(running.baseUrl, "/api/me", cookie);
      assert.equal(me.status, 200);
      const body = await me.json();
      assert.equal(body.email, email);
      assert.equal(body.tier, "free");
      assert.equal("passwordHash" in body, false);
      assert.equal(JSON.stringify(body).includes("password_hash"), false);
      assert.equal(JSON.stringify(body).includes(originalPassword), false);
    });

    await stopServer(running.child);
    running = await startServer(port);

    let sessionCookie;
    await t.test("signs in after a process restart", async () => {
      const response = await form(running.baseUrl, "/__auth/login", {
        email,
        password: originalPassword,
      });
      assert.equal(response.status, 302);
      sessionCookie = cookieFrom(response);
      const me = await runningFetch(running.baseUrl, "/api/me", sessionCookie);
      assert.equal(me.status, 200);
      const body = await me.json();
      assert.equal(body.email, email);
      assert.equal("passwordHash" in body, false);
    });

    await t.test("rejects an expired session and logout invalidates a live session", async () => {
      const rawToken = sessionCookie.split("=")[1];
      await sql`UPDATE dispatch_sessions SET expires_at=NOW() - INTERVAL '1 second' WHERE token_hash=${tokenHash(rawToken)}`;
      const expired = await runningFetch(running.baseUrl, "/api/me", sessionCookie);
      assert.deepEqual(await expired.json(), { tier: "free", billingPortal: false });

      const login = await form(running.baseUrl, "/__auth/login", {
        email,
        password: originalPassword,
      });
      const freshCookie = cookieFrom(login);
      const logout = await fetch(`${running.baseUrl}/__auth/logout`, {
        redirect: "manual",
        headers: { Cookie: freshCookie },
      });
      assert.equal(logout.status, 302);
      const afterLogout = await runningFetch(running.baseUrl, "/api/me", freshCookie);
      assert.deepEqual(await afterLogout.json(), { tier: "free", billingPortal: false });
    });

    let resetToken;
    await t.test("resets the password once and rejects a reused token", async () => {
      const recovery = await form(running.baseUrl, "/__auth/recover", { email });
      assert.equal(recovery.status, 200);
      resetToken = resetTokenFrom(await recovery.text());

      const reset = await form(running.baseUrl, "/__auth/reset", {
        token: resetToken,
        password: recoveredPassword,
      });
      assert.equal(reset.status, 200);
      assert.match(await reset.text(), /PASSWORD UPDATED/);

      const reused = await form(running.baseUrl, "/__auth/reset", {
        token: resetToken,
        password: "Another-password-789",
      });
      assert.equal(reused.status, 200);
      assert.match(await reused.text(), /Reset link expired/);

      const oldLogin = await form(running.baseUrl, "/__auth/login", {
        email,
        password: originalPassword,
      });
      assert.match(await oldLogin.text(), /Sign in failed/);
      const newLogin = await form(running.baseUrl, "/__auth/login", {
        email,
        password: recoveredPassword,
      });
      assert.equal(newLogin.status, 302);
    });

    await t.test("rejects an expired reset token", async () => {
      const recovery = await form(running.baseUrl, "/__auth/recover", { email });
      const expiredToken = resetTokenFrom(await recovery.text());
      await sql`UPDATE dispatch_password_resets SET expires_at=NOW() - INTERVAL '1 second' WHERE token_hash=${tokenHash(expiredToken)}`;
      const expired = await form(running.baseUrl, "/__auth/reset", {
        token: expiredToken,
        password: "Expired-password-999",
      });
      assert.equal(expired.status, 200);
      assert.match(await expired.text(), /Reset link expired/);
    });
  } finally {
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    await cleanupAccountFlow({ cleanup });
  }
});

test("removes a temporary database when isolated setup fails", async () => {
  temporaryDatabaseName = undefined;
  databaseUrl = undefined;
  const commands = [];
  let dropAttempts = 0;
  const run = async (command, args) => {
    commands.push({ command, args });
    if (command === "createdb") return;
    dropAttempts += 1;
    if (dropAttempts === 2) return;
    throw new Error("unexpected command");
  };

  await assert.rejects(
    prepareTestDatabase({
      run,
      env: { PGHOST: "127.0.0.1" },
      applicationUrl: "not-a-database-url",
      configuredUrl: undefined,
    }),
    /Unable to create the isolated auth test database/
  );

  assert.deepEqual(commands.map(({ command }) => command), ["createdb", "dropdb"]);
  assert.equal(commands[1].args[0], "--if-exists");
  assert.equal(temporaryDatabaseName, commands[0].args.at(-1));

  await removeTestDatabase({ run, env: { PGHOST: "127.0.0.1" } });
  assert.deepEqual(commands.map(({ command }) => command), ["createdb", "dropdb", "dropdb"]);
  assert.equal(commands[1].args.at(-1), commands[2].args.at(-1));
  assert.equal(temporaryDatabaseName, undefined);
});

test("removes a temporary database when auth startup fails", async () => {
  temporaryDatabaseName = undefined;
  databaseUrl = undefined;
  const commands = [];
  const env = { PGHOST: "127.0.0.1" };
  const run = async (command, args) => {
    commands.push({ command, args });
    if (command === "dropdb") {
      throw new Error("simulated dropdb failure");
    }
  };
  const failedChild = Object.assign(new EventEmitter(), {
    exitCode: 1,
    stderr: new EventEmitter(),
    kill() {},
  });

  let startupError;
  try {
    await prepareTestDatabase({
      run,
      env,
      applicationUrl: "postgresql://localhost/postgres",
      configuredUrl: undefined,
    });

    await startServer(1, { spawnProcess: () => failedChild });
  } catch (error) {
    startupError = error;
  }

  let cleanupError;
  try {
    await removeTestDatabase({ run, env });
  } catch (error) {
    cleanupError = error;
  }

  assert.match(startupError?.message || "", /server exited during startup with code 1/);
  assert.match(cleanupError?.message || "", /Unable to remove the isolated auth test database: simulated dropdb failure/);
  const combinedError = `${startupError?.message}; cleanup failed: ${cleanupError?.message}`;
  assert.match(combinedError, /server exited during startup with code 1/);
  assert.match(combinedError, /cleanup failed: Unable to remove the isolated auth test database: simulated dropdb failure/);
  assert.deepEqual(commands.map(({ command }) => command), ["createdb", "dropdb"]);
  assert.equal(commands[1].args[0], "--if-exists");
  assert.equal(commands[0].args.at(-1), commands[1].args.at(-1));
  assert.equal(temporaryDatabaseName, commands[0].args.at(-1));

  await removeTestDatabase({
    run: async (command, args) => {
      commands.push({ command, args });
    },
    env,
  });

  assert.deepEqual(commands.map(({ command }) => command), ["createdb", "dropdb", "dropdb"]);
  assert.equal(commands[1].args.at(-1), commands[2].args.at(-1));
  assert.equal(temporaryDatabaseName, undefined);
});

test("keeps the account-flow failure when database cleanup also fails", async () => {
  const commands = [];
  let accountCleanupAttempted = false;
  temporaryDatabaseName = "dispatch_auth_account_flow_failure";
  const remove = () => removeTestDatabase({
    run: async (command, args) => {
      commands.push({ command, args });
      throw new Error("simulated SQL cleanup failure");
    },
    env: { PGHOST: "127.0.0.1" },
  });

  await assert.rejects(
    cleanupAccountFlow({
      cleanup: async () => {
        accountCleanupAttempted = true;
        throw new Error("simulated account-flow failure");
      },
      remove,
    }),
    error => {
      assert.match(error.message, /simulated account-flow failure/);
      assert.match(error.message, /cleanup failed: Unable to remove the isolated auth test database: simulated SQL cleanup failure/);
      return true;
    }
  );

  assert.equal(accountCleanupAttempted, true);
  assert.deepEqual(commands.map(({ command }) => command), ["dropdb"]);
  assert.equal(commands[0].args.at(-1), "dispatch_auth_account_flow_failure");
  assert.equal(temporaryDatabaseName, "dispatch_auth_account_flow_failure");
});

test("keeps the account-flow failure when database cleanup succeeds", async () => {
  const commands = [];
  let accountCleanupAttempted = false;
  const accountError = new Error("simulated account-flow failure");
  temporaryDatabaseName = "dispatch_auth_account_flow_successful_cleanup";

  await assert.rejects(
    cleanupAccountFlow({
      cleanup: async () => {
        accountCleanupAttempted = true;
        throw accountError;
      },
      remove: () => removeTestDatabase({
        run: async (command, args) => {
          commands.push({ command, args });
        },
        env: { PGHOST: "127.0.0.1" },
      }),
    }),
    error => {
      assert.equal(error, accountError);
      assert.equal(error.message, "simulated account-flow failure");
      return true;
    }
  );

  assert.equal(accountCleanupAttempted, true);
  assert.deepEqual(commands.map(({ command }) => command), ["dropdb"]);
  assert.equal(commands[0].args.at(-1), "dispatch_auth_account_flow_successful_cleanup");
  assert.equal(temporaryDatabaseName, undefined);
});

test("surfaces the database cleanup failure when account cleanup succeeds", async () => {
  const commands = [];
  let accountCleanupAttempted = false;
  temporaryDatabaseName = "dispatch_auth_account_flow_database_cleanup_failure";

  await assert.rejects(
    cleanupAccountFlow({
      cleanup: async () => {
        accountCleanupAttempted = true;
      },
      remove: () => removeTestDatabase({
        run: async (command, args) => {
          commands.push({ command, args });
          throw new Error("simulated SQL cleanup failure");
        },
        env: { PGHOST: "127.0.0.1" },
      }),
    }),
    error => {
      assert.equal(
        error.message,
        "Unable to remove the isolated auth test database: simulated SQL cleanup failure"
      );
      return true;
    }
  );

  assert.equal(accountCleanupAttempted, true);
  assert.deepEqual(commands.map(({ command }) => command), ["dropdb"]);
  assert.equal(commands[0].args.at(-1), "dispatch_auth_account_flow_database_cleanup_failure");
  assert.equal(temporaryDatabaseName, "dispatch_auth_account_flow_database_cleanup_failure");
});

async function runSignalProbe({
  cleanupFails = false,
  signalToSend = "SIGTERM",
  secondSignal,
  cleanupDelayMs,
} = {}) {
  const markerPath = path.join(
    os.tmpdir(),
    `dispatch-auth-signal-${process.pid}-${crypto.randomUUID()}.log`
  );
  const child = spawn(process.execPath, [__filename], {
    env: {
      ...process.env,
      AUTH_TEST_DATABASE_URL: "",
      AUTH_TEST_SIGNAL_PROBE: "1",
      AUTH_TEST_SIGNAL_MARKER: markerPath,
      ...(cleanupFails ? { AUTH_TEST_SIGNAL_CLEANUP_FAILURE: "1" } : {}),
      ...(cleanupDelayMs ? { AUTH_TEST_SIGNAL_CLEANUP_DELAY_MS: String(cleanupDelayMs) } : {}),
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timed out waiting for signal probe\n${output}`)), 10_000);
    child.stdout.on("data", chunk => {
      output += chunk.toString();
      if (output.includes("ready\n")) {
        clearTimeout(timer);
        resolve();
      }
    });
    child.once("error", error => {
      clearTimeout(timer);
      reject(error);
    });
    child.once("exit", code => {
      if (!output.includes("ready\n")) {
        clearTimeout(timer);
        reject(new Error(`signal probe exited before setup completed (${code})\n${output}`));
      }
    });
  });

  try {
    await ready;
    child.kill(signalToSend);
    if (secondSignal) {
      await new Promise(resolve => setTimeout(resolve, 25));
      child.kill(secondSignal);
    }
    const [code, signal] = await new Promise(resolve => child.once("exit", (exitCode, exitSignal) => resolve([exitCode, exitSignal])));
    const events = fs.readFileSync(markerPath, "utf8").trim().split("\n");
    return { code, signal, events };
  } finally {
    if (child.exitCode === null) child.kill("SIGKILL");
    fs.rmSync(markerPath, { force: true });
  }
}

test("removes a temporary database when the test process is interrupted", async () => {
  const { code, signal, events } = await runSignalProbe();
  assert.equal(signal, null);
  assert.equal(code, 143);
  assert.equal(events.length, 4);
  assert.match(events[0], /^createdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[1], "ready");
  assert.match(events[2], /^dropdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[0].replace("createdb", "dropdb"), events[2]);
  assert.equal(events[3], "cleanup complete");
});

test("uses the SIGINT exit code when the test process is interrupted", async () => {
  const { code, signal, events } = await runSignalProbe({ signalToSend: "SIGINT" });
  assert.equal(signal, null);
  assert.equal(code, 130);
  assert.equal(events.length, 4);
  assert.match(events[0], /^createdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[1], "ready");
  assert.match(events[2], /^dropdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[0].replace("createdb", "dropdb"), events[2]);
  assert.equal(events[3], "cleanup complete");
});

test("ignores a second signal while forced-shutdown cleanup is in progress", async () => {
  const { code, signal, events } = await runSignalProbe({
    cleanupDelayMs: 100,
    secondSignal: "SIGINT",
  });
  assert.equal(signal, null);
  assert.equal(code, 143);
  assert.equal(events.length, 4);
  assert.match(events[0], /^createdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[1], "ready");
  assert.match(events[2], /^dropdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[0].replace("createdb", "dropdb"), events[2]);
  assert.equal(events[3], "cleanup complete");
});

test("reports a temporary database removal failure when the test process is interrupted", async () => {
  const { code, signal, events } = await runSignalProbe({ cleanupFails: true });
  assert.equal(signal, null);
  assert.equal(code, 143);
  assert.equal(events.length, 4);
  assert.match(events[0], /^createdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[1], "ready");
  assert.match(events[2], /^dropdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[0].replace("createdb", "dropdb"), events[2]);
  assert.equal(
    events[3],
    "cleanup failed: Unable to remove the isolated auth test database: simulated dropdb failure"
  );
});

test("uses the SIGINT exit code when cleanup fails during interruption", async () => {
  const { code, signal, events } = await runSignalProbe({
    cleanupFails: true,
    signalToSend: "SIGINT",
  });
  assert.equal(signal, null);
  assert.equal(code, 130);
  assert.equal(events.length, 4);
  assert.match(events[0], /^createdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[1], "ready");
  assert.match(events[2], /^dropdb dispatch_auth_test_\d+_\d+$/);
  assert.equal(events[0].replace("createdb", "dropdb"), events[2]);
  assert.equal(
    events[3],
    "cleanup failed: Unable to remove the isolated auth test database: simulated dropdb failure"
  );
});

async function runningFetch(baseUrl, pathname, cookie) {
  return fetch(`${baseUrl}${pathname}`, {
    headers: { Cookie: cookie },
  });
}