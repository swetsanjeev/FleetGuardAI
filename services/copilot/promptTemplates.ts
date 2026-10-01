export const PROMPTS = {
  SYSTEM: "You are FleetGuard AI Copilot, an assistant for connected-vehicle fleet operators.",
  RISK: (vin: string) => `Summarize risk factors for vehicle ${vin}.`,
  MAINTENANCE: (vin: string) => `Predict upcoming maintenance work for ${vin}.`,
};
