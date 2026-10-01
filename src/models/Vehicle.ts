export class VehicleModel {
  constructor(public vin: string, public name: string, public batterySoc: number) {}
  isLowBattery() { return this.batterySoc < 20; }
}
