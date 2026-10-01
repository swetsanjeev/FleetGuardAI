import { Kafka } from "kafkajs";
import { kafkaConfig } from "../../config/kafka.config";

export async function consume(topic: string, handler: (value: string) => void) {
  const kafka = new Kafka(kafkaConfig);
  const consumer = kafka.consumer({ groupId: kafkaConfig.groupId });
  await consumer.connect();
  await consumer.subscribe({ topic });
  await consumer.run({ eachMessage: async ({ message }) => handler(message.value?.toString() ?? "") });
}
