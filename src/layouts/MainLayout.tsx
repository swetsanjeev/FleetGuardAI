import React from "react";

export function MainLayout({ children }: { children: React.ReactNode }) {
  return <div className="main-layout"><nav>FleetGuard AI</nav><main>{children}</main></div>;
}
