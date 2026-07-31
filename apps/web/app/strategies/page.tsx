import type { Metadata } from "next";
import { StrategiesView } from "../views/StrategiesView";

export const metadata: Metadata = { title: "策略實驗室" };

export default function StrategiesPage() { return <StrategiesView />; }
