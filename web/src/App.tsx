import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Atlas } from "./routes/Atlas";
import { Methods } from "./routes/Methods";
import { NotFound } from "./routes/NotFound";
import { Overview } from "./routes/Overview";
import { Rankings } from "./routes/Rankings";
import { Species } from "./routes/Species";

export function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
      <Routes>
        <Route path="/" element={<Layout><Overview /></Layout>} />
        <Route path="/atlas" element={<Layout bleed><Atlas /></Layout>} />
        <Route path="/rankings" element={<Layout><Rankings /></Layout>} />
        <Route path="/species/:slug" element={<Layout><Species /></Layout>} />
        <Route path="/methods" element={<Layout><Methods /></Layout>} />
        <Route path="*" element={<Layout><NotFound /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}
