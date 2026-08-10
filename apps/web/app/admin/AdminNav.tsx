"use client";
import Link from "next/link";
const links = [["/admin", "Dashboard"], ["/admin/schema", "ERD"], ["/admin/instruments", "Instruments"], ["/admin/topics", "Topics"], ["/admin/relations", "Relations"], ["/admin/imports", "Imports"]];
export function AdminNav() { return <nav className="adminNav">{links.map(([href, label]) => <Link href={href} key={href}>{label}</Link>)}</nav>; }
