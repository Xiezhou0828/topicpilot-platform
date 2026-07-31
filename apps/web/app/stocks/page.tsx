import type { Metadata } from "next";
import { StocksView } from "../views/StocksView";

export const metadata: Metadata = { title: "股票宇宙" };

export default function StocksPage() { return <StocksView />; }
