export class AlertModel {
  constructor(public id: string, public message: string, public severity: string) {}
  isCritical() { return this.severity === "critical"; }
}
