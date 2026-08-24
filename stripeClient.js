const Stripe = require("stripe");
const { StripeSync } = require("stripe-replit-sync");

const DISPATCH_PLAN = "dispatch_premium_monthly";

/**
 * Fetches connection credentials for each use so key rotation is picked up
 * without restarting the application.
 */
async function getStripeCredentials() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const token = process.env.REPL_IDENTITY
    ? `repl ${process.env.REPL_IDENTITY}`
    : process.env.WEB_REPL_RENEWAL
      ? `depl ${process.env.WEB_REPL_RENEWAL}`
      : null;

  if (!hostname || !token) {
    throw new Error("Stripe is not connected to this Replit environment.");
  }

  const response = await fetch(
    `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=stripe`,
    {
      headers: { Accept: "application/json", X_REPLIT_TOKEN: token },
      signal: AbortSignal.timeout(10_000),
    },
  );
  if (!response.ok) throw new Error(`Unable to load Stripe connection (${response.status}).`);

  const data = await response.json();
  const settings = data.items?.[0]?.settings;
  const secretKey = settings?.secret_key || settings?.secret;
  if (!secretKey) throw new Error("The Stripe connection has no secret key.");

  return { secretKey, webhookSecret: settings.webhook_secret };
}

async function getUncachableStripeClient() {
  const { secretKey } = await getStripeCredentials();
  return new Stripe(secretKey);
}

async function getStripeSync() {
  if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required for Stripe sync.");
  const { secretKey, webhookSecret } = await getStripeCredentials();
  return new StripeSync({
    poolConfig: { connectionString: process.env.DATABASE_URL, max: 5 },
    stripeSecretKey: secretKey,
    stripeWebhookSecret: webhookSecret || "",
  });
}

async function getStripeMode() {
  const { secretKey } = await getStripeCredentials();
  return secretKey.startsWith("sk_live_") ? "live" : "test";
}

/**
 * Creates the only sellable membership product idempotently in each Stripe mode.
 * Product and price records always originate in Stripe, never the database.
 */
async function ensureDispatchPremiumPrice() {
  const stripe = await getUncachableStripeClient();
  const products = await stripe.products.list({ active: true, limit: 100 });
  let product = products.data.find(item => item.metadata?.dispatch_plan === DISPATCH_PLAN);

  if (!product) {
    product = await stripe.products.create({
      name: "Dispatch Premium",
      description: "AI briefs, market lenses, portfolio analysis, and Dispatch Expert.",
      metadata: { dispatch_plan: DISPATCH_PLAN },
    });
  }

  const prices = await stripe.prices.list({ product: product.id, active: true, limit: 100 });
  let price = prices.data.find(item =>
    item.currency === "gbp"
    && item.unit_amount === 1500
    && item.recurring?.interval === "month",
  );

  if (!price) {
    price = await stripe.prices.create({
      product: product.id,
      unit_amount: 1500,
      currency: "gbp",
      recurring: { interval: "month" },
      metadata: { dispatch_plan: DISPATCH_PLAN },
    });
  }

  return price;
}

module.exports = {
  DISPATCH_PLAN,
  ensureDispatchPremiumPrice,
  getStripeCredentials,
  getStripeMode,
  getStripeSync,
  getUncachableStripeClient,
};