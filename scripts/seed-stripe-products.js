const { ensureDispatchPremiumPrice } = require("../stripeClient");

async function seed() {
  const price = await ensureDispatchPremiumPrice();
  console.log(`Dispatch Premium monthly price ready: ${price.id}`);
}

seed().catch(error => {
  console.error("Unable to prepare Dispatch Premium:", error.message);
  process.exitCode = 1;
});