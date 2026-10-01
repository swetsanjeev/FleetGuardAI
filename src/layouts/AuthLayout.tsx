import React from "react";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return <div className="auth-layout"><div className="card">{children}</div></div>;
}
