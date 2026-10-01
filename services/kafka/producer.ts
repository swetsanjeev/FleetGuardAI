import { Kafka } from "kafkajs";
import { kafkaConfig } from "../../config/kafka.config";

const kafka = new Kafka(kafkaConfig);
export const producer = kafka.producer();

export async function publishTelemetry(topic: string, vin: string, payload: unknown) {
  await producer.connect();
  await producer.send({ topic, messages: [{ key: vin, value: JSON.stringify(payload) }] });
}
