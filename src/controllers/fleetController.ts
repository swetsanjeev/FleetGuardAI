import { fleetService } from "../services/fleetService";

export async function listFleets() { return fleetService.list(); }
