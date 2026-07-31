import type { Metadata } from "next";
import { TopicsView } from "../views/TopicsView";

export const metadata: Metadata = { title: "題材輪動" };

export default function TopicsPage() { return <TopicsView />; }
