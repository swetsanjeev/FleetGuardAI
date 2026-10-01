import './globals.css';

export const metadata = {
  title: 'FleetGuard AI',
  description: 'Fleet operations platform',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}