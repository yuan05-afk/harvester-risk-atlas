import { MotionConfig } from "motion/react";
import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Preloader, shouldPlayIntro } from "./components/Preloader";
import { Loading } from "./components/Status";
import { NotFound } from "./routes/NotFound";
import { Overview } from "./routes/Overview";

// Every page but the first loads when it is opened.
const Atlas = lazy(() => import("./routes/Atlas").then((m) => ({ default: m.Atlas })));
const Brief = lazy(() => import("./routes/Brief").then((m) => ({ default: m.Brief })));
const HowItWorks = lazy(() => import("./routes/HowItWorks").then((m) => ({ default: m.HowItWorks })));
const Plants = lazy(() => import("./routes/Plants").then((m) => ({ default: m.Plants })));
const Species = lazy(() => import("./routes/Species").then((m) => ({ default: m.Species })));

function Shell() {
  const location = useLocation();
  // The intro opens the Overview only; deep links go straight to their page.
  const [intro, setIntro] = useState(() => location.pathname === "/" && shouldPlayIntro());
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout><Overview /></Layout>} />
        <Route path="/atlas" element={<Layout bleed><Atlas /></Layout>} />
        <Route path="/plants" element={<Layout><Plants /></Layout>} />
        <Route path="/rankings" element={<Navigate to="/plants" replace />} />
        <Route path="/species/:slug" element={<Layout><Species /></Layout>} />
        <Route
          path="/species/:slug/brief"
          element={
            <Suspense fallback={<Loading />}>
              <Brief />
            </Suspense>
          }
        />
        <Route path="/how-it-works" element={<Layout><HowItWorks /></Layout>} />
        <Route path="/methods" element={<Navigate to="/how-it-works" replace />} />
        <Route path="*" element={<Layout><NotFound /></Layout>} />
      </Routes>
      {intro ? <Preloader onDone={() => setIntro(false)} /> : null}
    </>
  );
}

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
        <Shell />
      </BrowserRouter>
    </MotionConfig>
  );
}
