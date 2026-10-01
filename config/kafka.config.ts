export const kafkaConfig = {
  brokers: (process.env.KAFKA_BROKERS ?? "localhost:9092").split(","),
  clientId: "fleetguard-api",
  groupId: "fleetguard-consumers",
};
