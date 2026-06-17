import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface Props {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export default function Layout({ title, subtitle, children }: Props) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 max-w-[1500px]">
        <Header title={title} subtitle={subtitle} />
        <div className="mt-5 flex flex-col gap-5">{children}</div>
        <div className="text-center text-[12px] text-tv-muted/70 font-semibold mt-8 mb-2">
          TrafficVision AI • Built for Smart-City Traffic Enforcement
        </div>
      </main>
    </div>
  );
}
