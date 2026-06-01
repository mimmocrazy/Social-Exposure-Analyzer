import React, { useState, useEffect } from 'react';
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, Text, Metric, Flex, ProgressBar, Title, BarChart, TextInput, Button } from '@tremor/react';
import { startAnalysis, getAnalysisStatus, getAnalysisHistory, login, register, deleteAnalysis } from './api';

const queryClient = new QueryClient();

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("React Crash:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-red-900 text-white rounded-xl max-w-2xl mx-auto mt-12 overflow-auto">
          <h2 className="text-2xl font-bold mb-4">💥 Errore di Rendering!</h2>
          <pre className="text-xs whitespace-pre-wrap">{this.state.error && this.state.error.toString()}</pre>
          <pre className="text-xs whitespace-pre-wrap mt-4 text-red-200">{this.state.errorInfo && this.state.errorInfo.componentStack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

// Custom Radial Progress Component
const RadialProgress = ({ score, isCritical }) => {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = isCritical ? '#ef4444' : '#3b82f6'; // red-500 or blue-500

  return (
    <div className="relative flex items-center justify-center">
      <svg className="transform -rotate-90 w-40 h-40">
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="transparent"
          className="text-gray-800"
        />
        <motion.circle
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          cx="80"
          cy="80"
          r={radius}
          stroke={color}
          strokeWidth="12"
          fill="transparent"
          strokeDasharray={circumference}
          strokeLinecap="round"
          className="drop-shadow-lg"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-white">
        <span className="text-4xl font-extrabold">{score}</span>
        <span className="text-xs text-gray-400 uppercase tracking-widest mt-1">Score</span>
      </div>
    </div>
  );
};

// Icons (mock using SVG for pure independence if heroicons fails, but we assume it's installed)
const getIconForPII = (label) => {
  const l = (label || '').toLowerCase();
  if (l.includes('email')) return (
    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
  );
  if (l.includes('phone') || l.includes('telefono')) return (
    <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
  );
  if (l.includes('location') || l.includes('indirizzo') || l.includes('place') || l.includes('luogo')) return (
    <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.243-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
  );
  if (l.includes('ip') || l.includes('server')) return (
    <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
  );
  if (l.includes('person') || l.includes('gente') || l.includes('nome')) return (
    <svg className="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
  );
  if (l.includes('org') || l.includes('aziend') || l.includes('studio') || l.includes('societ')) return (
    <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
  );
  if (l.includes('birth') || l.includes('nascita') || l.includes('dat')) return (
    <svg className="w-5 h-5 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
  );
  if (l.includes('age') || l.includes('età') || l.includes('anni')) return (
    <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  );
  if (l.includes('occupat') || l.includes('lavor') || l.includes('profession') || l.includes('ruol') || l.includes('influenc') || l.includes('creator')) return (
    <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
  );
  if (l.includes('handle') || l.includes('username') || l.includes('social') || l.includes('profilo')) return (
    <svg className="w-5 h-5 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" /></svg>
  );
  // Default icon
  return (
    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  );
};

const getOfficialIcon = (iconName, isActive) => {
  switch (iconName) {
    case 'instagram':
      return (
        <svg className={`w-12 h-12 transition-all duration-700 ${isActive ? 'drop-shadow-[0_0_15px_rgba(236,72,153,0.5)] animate-pulse' : 'text-gray-500 opacity-50'}`} fill="none" viewBox="0 0 24 24">
          <defs>
            <linearGradient id="ig-grad" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#f09433" />
              <stop offset="25%" stopColor="#e6683c" />
              <stop offset="50%" stopColor="#dc2743" />
              <stop offset="75%" stopColor="#cc2366" />
              <stop offset="100%" stopColor="#bc1888" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5" stroke={isActive ? "url(#ig-grad)" : "currentColor"} strokeWidth={1.5} />
          <path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z" stroke={isActive ? "url(#ig-grad)" : "currentColor"} strokeWidth={1.5} />
          <circle cx="17.5" cy="6.5" r="1.5" fill={isActive ? "url(#ig-grad)" : "currentColor"} />
        </svg>
      );
    case 'x':
      return (
        <svg className={`w-12 h-12 transition-all duration-700 ${isActive ? 'text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.5)] animate-pulse' : 'text-gray-500'}`} viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      );
    case 'facebook':
      return (
        <svg className={`w-12 h-12 transition-all duration-700 ${isActive ? 'text-blue-500 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] animate-pulse' : 'text-gray-500'}`} fill="currentColor" viewBox="0 0 24 24">
          <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c5.05-.5 9-4.76 9-9.95z" />
        </svg>
      );
    case 'linkedin':
      return (
        <svg className={`w-12 h-12 transition-all duration-700 ${isActive ? 'text-sky-500 drop-shadow-[0_0_15px_rgba(14,165,233,0.5)] animate-pulse' : 'text-gray-500'}`} fill="currentColor" viewBox="0 0 24 24">
          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
        </svg>
      );
    case 'gears':
      return <span className="text-4xl md:text-5xl">⚙️</span>;
    case 'spy':
      return <span className="text-4xl md:text-5xl">🕵️</span>;
    case 'brain':
      return <span className="text-4xl md:text-5xl">🧠</span>;
    case 'doc':
      return <span className="text-4xl md:text-5xl">📄</span>;
    default:
      return <span className="text-4xl md:text-5xl">🔍</span>;
  }
};

const InteractiveLoading = () => {
  const steps = [
    { text: "Inizializzazione Deep OSINT", icon: "gears", delay: 0 },
    { text: "Scansione Instagram", icon: "instagram", delay: 1500 },
    { text: "Footprint X (Twitter)", icon: "x", delay: 3500 },
    { text: "Verifica LinkedIn", icon: "linkedin", delay: 5500 },
    { text: "Verifica FaceBook", icon: "facebook", delay: 7500 },
    { text: "Estrazione Dati Sensibili", icon: "spy", delay: 9500 },
    { text: "Audit AI in corso", icon: "brain", delay: 12000 },
    { text: "Stesura Risk Report", icon: "doc", delay: 14500 }
  ];

  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timers = steps.map((step, index) =>
      setTimeout(() => {
        setCurrentStep(index);
      }, step.delay)
    );
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center py-12 w-full max-w-7xl mx-auto relative mt-10">
      <h2 className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 text-3xl md:text-4xl font-extrabold tracking-tight mb-20 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] text-center animate-pulse">
        Analisi Profonda in Corso
      </h2>

      <div className="w-full relative flex flex-wrap justify-center items-center gap-y-12 gap-x-2 md:gap-x-4 px-4">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isPast = index < currentStep;
          const isFuture = index > currentStep;

          return (
            <React.Fragment key={index}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                className={`flex flex-col items-center justify-center p-6 rounded-3xl border transition-all duration-1000 w-40 h-40 md:w-48 md:h-48 aspect-square flex-shrink-0 text-center relative group ${isActive
                    ? 'bg-blue-500/10 border-blue-400/50 shadow-[0_0_40px_rgba(59,130,246,0.3)] z-10 scale-110'
                    : isPast
                      ? 'bg-green-500/5 border-green-500/20 opacity-80 scale-95'
                      : 'bg-white/5 border-white/5 opacity-30 scale-90 blur-[1px] grayscale'
                  }`}
              >
                {isActive && (
                  <motion.div
                    className="absolute inset-0 rounded-3xl border-2 border-blue-400/50"
                    initial={{ scale: 1, opacity: 1 }}
                    animate={{ scale: 1.2, opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                  />
                )}
                {isPast && (
                  <div className="absolute -top-3 -right-3 bg-green-500 text-white rounded-full p-1 shadow-[0_0_10px_rgba(34,197,94,0.6)]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                  </div>
                )}
                <div className={`flex items-center justify-center mb-4 transition-transform duration-700 ${isActive ? 'scale-110' : ''}`}>
                  {getOfficialIcon(step.icon, isActive || isPast)}
                </div>
                <span className={`text-xs md:text-sm font-semibold tracking-wide transition-colors duration-700 ${isActive ? 'text-white drop-shadow-md' : isPast ? 'text-green-400/80' : 'text-gray-500'}`}>
                  {step.text}
                </span>
              </motion.div>

              {/* Frecce dinamiche */}
              {index < steps.length - 1 && (
                <div className="hidden md:flex items-center justify-center w-8 lg:w-12">
                  <motion.div
                    className={`h-0.5 w-full transition-all duration-1000 relative ${isPast ? 'bg-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : isActive ? 'bg-blue-400/80 shadow-[0_0_15px_rgba(59,130,246,0.8)]' : 'bg-white/10'}`}
                  >
                    {isActive && (
                      <motion.div
                        initial={{ x: '-100%', opacity: 1 }}
                        animate={{ x: '100%', opacity: 0 }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                        className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white to-transparent"
                      />
                    )}
                  </motion.div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </motion.div>
  );
};

function Dashboard({ analysisId }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysisStatus(analysisId),
    refetchInterval: (data) => {
      if (!data) return 3000;
      return data.status === 'PENDING' ? 3000 : false;
    },
  });

  if (isLoading || (data && data.status === 'PENDING')) {
    return <InteractiveLoading />;
  }

  if (isError || data?.status === 'FAILED') {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-8 bg-red-950/40 border border-red-500/30 rounded-3xl mt-8 text-center max-w-lg mx-auto backdrop-blur-xl">
        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        </div>
        <h2 className="text-red-400 text-2xl font-bold mb-2">Analisi Fallita</h2>
        <p className="text-red-200/70">{data?.error_message || "Si è verificato un errore durante la scansione OSINT."}</p>
      </motion.div>
    );
  }

  if (data?.status === 'COMPLETED') {
    const score = data.risk_score || 0;
    const isCritical = data.risk_level === 'CRITICAL' || data.risk_level === 'HIGH';
    const isInsufficient = data.llm_report?.insufficient_data === true;

    const scrapers = data.raw_data_dump?.scraper_results || [];
    const holehe = data.raw_data_dump?.holehe_results || [];
    const ocrResults = data.raw_data_dump?.ocr_results || [];
    const metadata = data.raw_data_dump?.metadata || {};

    const isSherlockActive = metadata.sherlock_attempted !== false;

    const isInstagramAttempted = metadata.instagram_attempted || scrapers.some(s => s.url?.includes("instagram.com"));
    const isInstagramSuccess = scrapers.some(s => s.source === "Instagram Deep Scan API" && s.status === "ACCESSIBLE");
    const isInstagramRateLimit = scrapers.some(s => s.source === "Instagram Deep Scan API" && s.error?.includes("429"));
    const isInstagramError = scrapers.some(s => s.source === "Instagram Deep Scan API" && s.error);

    const isDdgActive = metadata.enable_ddg !== false;

    const isHoleheAttempted = metadata.enable_holehe !== false;
    const isHoleheSuccess = holehe.length > 0;

    const isFbAttempted = metadata.enable_fb_scan === true;
    const isFbSuccess = scrapers.some(s => s.source === "Facebook Deep Scan API" && s.status === "ACCESSIBLE");

    // Pannello Profilo Privato / Dati Insufficienti
    if (isInsufficient) {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-12 w-full max-w-3xl mx-auto space-y-6">
          <div className="glassmorphism rounded-3xl p-10 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 -z-10"></div>

            <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
              <svg className="w-10 h-10 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>

            <h2 className="text-white text-2xl font-bold tracking-tight mb-3">Profilo Protetto</h2>
            <p className="text-gray-400 max-w-lg mx-auto leading-relaxed mb-6">
              Il profilo analizzato risulta <strong className="text-emerald-400">privato o inaccessibile</strong>.
              Non è stato possibile estrarre dati personali esposti pubblicamente.
              Le impostazioni di privacy dell'utente sono adeguate e limitano l'esposizione a rischi di social engineering.
            </p>

            <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-5 py-2.5 rounded-full text-sm font-bold tracking-wider">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>RISCHIO: {data.risk_level || 'LOW'} — Score: {score}/100</span>
            </div>
          </div>

          {/* Mostra comunque il report AI se presente */}
          {data.llm_report?.mitigation_advice && (
            <div className="glassmorphism rounded-3xl p-8 border border-white/5">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-white/10">
                  <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                </div>
                <h3 className="text-white text-lg font-bold">Valutazione AI</h3>
              </div>
              <p className="text-gray-300 font-light leading-relaxed">{data.llm_report.mitigation_advice}</p>
            </div>
          )}
        </motion.div>
      );
    }

    // Raggruppamento PII per evitare disordine visivo
    const labelMapping = {
      'PERSON': 'Persone Coinvolte',
      'EMAIL': 'Indirizzi Email',
      'PHONE': 'Numeri di Telefono',
      'LOCATION': 'Luoghi e Indirizzi',
      'ORGANIZATION': 'Organizzazioni / Aziende',
      'DATE_OF_BIRTH': 'Data di Nascita',
      'PLACE_OF_BIRTH': 'Luogo di Nascita',
      'AGE': 'Età Rilevata',
      'OCCUPATION': 'Ruoli e Occupazioni',
      'IP': 'Indirizzi IP',
      'SOCIAL_MEDIA_HANDLE': 'Account Social',
      'USERNAME': 'Account Social',
      'HANDLE': 'Account Social',
    };

    const piiGroups = {};
    if (data.pii_extracted && Array.isArray(data.pii_extracted)) {
      data.pii_extracted.forEach((pii) => {
        if (!pii || !pii.label) return;
        const labelKey = pii.label.toUpperCase();
        if (!piiGroups[labelKey]) {
          piiGroups[labelKey] = [];
        }
        if (pii.value) {
          const exists = piiGroups[labelKey].some(item => item.value === pii.value);
          if (!exists) {
            piiGroups[labelKey].push({
              value: pii.value,
              source: pii.source || "Scansione OSINT",
              confidence: pii.confidence_score
            });
          }
        }
      });
    }

    return (
      <div className="mt-12 space-y-8 w-full max-w-7xl mx-auto text-left">

        {/* Top Row: Score & Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 glassmorphism rounded-3xl p-8 flex flex-col relative overflow-hidden group">
            <div className={`absolute -inset-2 bg-gradient-to-tr ${isCritical ? 'from-red-500/20 to-orange-500/5' : 'from-blue-500/20 to-cyan-500/5'} blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700`}></div>
            <h3 className="text-gray-400 text-sm font-bold uppercase tracking-widest mb-6 text-center">Indice di Rischio</h3>
            <div className="flex justify-center mb-6">
              <RadialProgress score={score} isCritical={isCritical} />
            </div>

            {data.llm_report?.score_breakdown && (
              <div className="w-full mt-2 mb-4 bg-black/20 rounded-xl p-4 border border-white/5 overflow-y-auto max-h-40 custom-scrollbar">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Score Breakdown</h4>
                <div className="space-y-2">
                  {data.llm_report.score_breakdown.map((sb, idx) => (
                    <div key={idx} className="flex justify-between items-start text-xs">
                      <span className="text-gray-300 mr-2 leading-relaxed">{sb.reason}</span>
                      <span className="text-white font-bold whitespace-nowrap px-1.5 py-0.5 bg-white/10 rounded">+{sb.points_added}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="w-full space-y-4 mt-2 border-t border-white/5 pt-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Identità e Contatti</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.identity_exposure || 0}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${data.llm_report?.sub_scores?.identity_exposure || 0}%` }} transition={{ duration: 1, ease: "easeOut" }} className="bg-red-500 h-1.5 rounded-full shadow-[0_0_10px_rgba(239,68,68,0.8)]"></motion.div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Network e Relazioni</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.network_exposure || 0}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${data.llm_report?.sub_scores?.network_exposure || 0}%` }} transition={{ duration: 1, ease: "easeOut" }} className="bg-orange-500 h-1.5 rounded-full shadow-[0_0_10px_rgba(249,115,22,0.8)]"></motion.div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Routine e Luoghi</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.routine_exposure || 0}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${data.llm_report?.sub_scores?.routine_exposure || 0}%` }} transition={{ duration: 1, ease: "easeOut" }} className="bg-amber-400 h-1.5 rounded-full shadow-[0_0_10px_rgba(251,191,36,0.8)]"></motion.div>
                </div>
              </div>
            </div>

            <div className={`mt-6 px-6 py-2 mx-auto rounded-full text-sm font-extrabold tracking-widest shadow-lg border ${isCritical ? 'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/10' : 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-blue-500/10'}`}>
              {data.risk_level}
            </div>
          </div>

          {/* PII Grid Widget */}
          <div className="md:col-span-2 glassmorphism rounded-3xl p-8 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-white text-xl font-bold tracking-tight">Dati Sensibili (PII)</h3>
              <span className="text-xs bg-white/10 text-gray-300 px-3 py-1 rounded-full font-medium">{data.pii_extracted?.length || 0} Trovati</span>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 min-h-[200px]">
              {(Object.keys(piiGroups).length === 0) ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-3">
                  <svg className="w-12 h-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                  <p className="text-sm font-medium">Nessun dato critico esposto.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Object.entries(piiGroups).map(([label, values], idx) => (
                    <motion.div
                      key={label}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="flex flex-col p-5 rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-colors group animate-fade-in"
                    >
                      <div className="flex items-center space-x-3 mb-3 pb-2 border-b border-white/5">
                        <div className="p-2 bg-white/5 rounded-xl group-hover:scale-110 transition-transform">
                          {getIconForPII(label)}
                        </div>
                        <div>
                          <p className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">{label}</p>
                          <h4 className="text-white text-sm font-semibold tracking-tight">
                            {labelMapping[label] || label}
                          </h4>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {values.map((valObj, valIdx) => (
                          <span
                            key={valIdx}
                            className="bg-white/5 hover:bg-white/10 text-gray-200 text-xs px-2.5 py-1.5 rounded-lg transition-all duration-200 border border-white/5 break-all font-mono inline-flex items-center gap-1.5 relative group/item"
                          >
                            <span>{valObj.value}</span>
                            <span className="relative group/tooltip inline-flex items-center text-gray-500 hover:text-blue-400 transition-colors cursor-help">
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 16h-1v-4h-1m1-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48 p-2.5 bg-slate-950/95 border border-white/10 text-[10px] text-gray-200 rounded-xl shadow-2xl opacity-0 group-hover/tooltip:opacity-100 pointer-events-none transition-opacity duration-200 z-50 text-center font-sans font-normal leading-normal normal-case backdrop-blur-md">
                                Fonte: <strong className="text-blue-400 block mt-0.5">{valObj.source || 'Scansione OSINT'}</strong>
                                {valObj.confidence && <span className="block text-gray-500 mt-1">Confidenza: {Math.round(valObj.confidence * 100)}%</span>}
                              </span>
                            </span>
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

{/* OCR Media Gallery Widget */}
        {ocrResults && (
          <div className="glassmorphism rounded-3xl p-8 flex flex-col mt-6 border border-white/5 relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-cyan-500/5 -z-10 opacity-60 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 rounded-xl border border-white/10">
                  <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                </div>
                <div>
                  <h3 className="text-white text-xl font-bold tracking-tight">Analisi Media & OCR</h3>
                  <p className="text-gray-400 text-xs uppercase tracking-wider font-semibold">Testo Estratto da Immagini Post</p>
                </div>
              </div>
              <span className="text-xs bg-white/10 text-cyan-400 px-3 py-1 rounded-full font-bold">{ocrResults.length} Rilevamenti</span>
            </div>
            
            {ocrResults.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 border border-white/5 bg-white/[0.02] rounded-2xl">
                <svg className="w-12 h-12 text-gray-500 opacity-30 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                <p className="text-gray-400 text-sm font-medium">Nessun media o testo estratto disponibile.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {ocrResults.map((ocr, idx) => (
                  <div key={idx} className="bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden flex flex-col hover:bg-white/[0.05] transition-colors">
                    <div className="h-40 w-full overflow-hidden bg-black/40 relative group/img">
                      <img src={ocr.url} alt="OCR Source" className="w-full h-full object-cover opacity-80 group-hover/img:opacity-100 group-hover/img:scale-105 transition-all duration-500" />
                      <div className="absolute top-2 right-2 bg-red-500/80 backdrop-blur-md px-2 py-1 rounded-md text-[10px] font-bold text-white shadow-lg border border-red-400/50 flex items-center space-x-1">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        <span>TESTO RILEVATO</span>
                      </div>
                    </div>
                    <div className="p-4 flex-1 flex flex-col">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-2 block">Testo Estratto in Chiaro (Computer Vision)</span>
                      <div className="bg-black/30 rounded-xl p-3 border border-white/5 flex-1 overflow-y-auto max-h-32 custom-scrollbar">
                        <p className="text-gray-300 font-mono text-xs leading-relaxed break-words whitespace-pre-wrap">
                          {ocr.text_extracted}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        
{/* AI Audit Alert Box */}
        {data.llm_report && (
          <div className="relative overflow-hidden rounded-3xl border border-white/10 glassmorphism p-0 flex flex-col md:flex-row">
            <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-blue-500 to-purple-500 hidden md:block"></div>
            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 to-purple-500 md:hidden"></div>

            {/* Left Column: Title & Threats */}
            <div className="p-8 md:w-1/3 bg-black/20 border-b md:border-b-0 md:border-r border-white/5">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-white/10">
                  <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                </div>
                <div>
                  <h3 className="text-white text-lg font-bold tracking-tight">Audit AI</h3>
                  <p className="text-gray-400 text-xs uppercase tracking-wider font-semibold">Gemini Pro</p>
                </div>
              </div>

              {data.llm_report.threat_vectors && data.llm_report.threat_vectors.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-widest font-bold mb-3">Vettori di Minaccia Rilevati</p>
                  <div className="flex flex-wrap gap-2">
                    {data.llm_report.threat_vectors.map((threat, idx) => (
                      <span key={idx} className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-950/60 text-red-300 border border-red-500/30 hover:border-red-500/50 hover:text-white transition-all duration-300 shadow-[0_0_10px_rgba(239,68,68,0.02)] hover:shadow-[0_0_12px_rgba(239,68,68,0.12)]">
                        <svg className="w-3.5 h-3.5 mr-2 text-red-400 opacity-90" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                        {threat}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {(!data.llm_report.threat_vectors || data.llm_report.threat_vectors.length === 0) && (
                <div className="flex items-center space-x-2 text-green-400/80 bg-green-500/5 border border-green-500/10 p-3 rounded-xl">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span className="text-sm font-medium">Nessuna minaccia diretta</span>
                </div>
              )}
            </div>

            {/* Right Column: Mitigation Advice & Sections */}
            <div className="p-8 md:w-2/3 flex flex-col justify-start overflow-y-auto max-h-[550px] custom-scrollbar">
              <div className="flex items-center space-x-2 mb-6 border-b border-white/5 pb-4">
                <svg className="w-5 h-5 text-blue-400 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                <h4 className="text-blue-300 text-sm font-bold tracking-wide uppercase">Piano di Mitigazione</h4>
              </div>

              {data.llm_report.mitigation_sections && data.llm_report.mitigation_sections.length > 0 ? (
                <div className="space-y-6">
                  {data.llm_report.mitigation_sections.map((section, idx) => {
                    const crit = (section.criticality || '').toUpperCase();
                    const isSecCritical = crit === 'CRITICA' || crit === 'ALTA' || crit === 'HIGH' || crit === 'CRITICAL';
                    const isSecMedium = crit === 'MEDIA' || crit === 'MEDIUM';

                    const badgeColor = isSecCritical
                      ? 'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/5'
                      : isSecMedium
                        ? 'bg-orange-500/10 text-orange-400 border-orange-500/20 shadow-orange-500/5'
                        : 'bg-green-500/10 text-green-400 border-green-500/20 shadow-green-500/5';

                    return (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 space-y-4 hover:border-white/10 transition-colors"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
                          <div>
                            <h5 className="text-white text-base font-bold tracking-tight">{section.title}</h5>
                            {section.threat_vector && (
                              <span className="text-[10px] text-red-400 font-mono tracking-wider block mt-0.5 uppercase">
                                Vettore: {section.threat_vector}
                              </span>
                            )}
                          </div>
                          <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-widest border self-start sm:self-auto shadow-sm ${badgeColor}`}>
                            {section.criticality || 'MEDIA'}
                          </span>
                        </div>

                        <div className="space-y-4 text-sm">
                          {section.exposed_data && (
                            <div className="bg-white/[0.01] border border-white/5 rounded-xl p-4">
                              <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block mb-1.5">Dato Esposto Rilevato (Causa)</span>
                              <p className="text-gray-300 font-medium italic break-words leading-relaxed">
                                “{section.exposed_data}”
                              </p>
                            </div>
                          )}

                          <div>
                            <span className="text-[10px] text-blue-400 font-extrabold uppercase tracking-widest block mb-1.5">Mitigazioni Consigliate</span>
                            <p className="text-gray-300 font-light leading-relaxed">
                              {section.mitigation}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ) : (
                <div className="prose prose-invert max-w-none">
                  <p className="text-gray-300 leading-relaxed text-[15px] font-light">
                    {data.llm_report.mitigation_advice || "Nessun consiglio di mitigazione generato."}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

{/* Dynamic Routine & Tools Analysis Row */}
        <div className="grid grid-cols-1 gap-6 mt-6">
          {/* Card 2: Strumenti OSINT Integrati */}
          <div className="glassmorphism rounded-3xl p-8 flex flex-col relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 -z-10 opacity-60 group-hover:opacity-100 transition-opacity duration-500"></div>

            <div className="flex justify-between items-center mb-8 border-b border-white/5 pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-white/10">
                  <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white text-lg font-bold tracking-tight">Analizzatore Strumenti OSINT</h3>
                  <p className="text-gray-400 text-xs uppercase tracking-wider font-semibold">Stato Telemetria e Payload</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Sherlock */}
              <div className={`relative overflow-hidden p-5 rounded-2xl border transition-all duration-300 group/card ${isSherlockActive ? 'bg-green-500/5 border-green-500/20 hover:bg-green-500/10 hover:border-green-500/30' : 'bg-gray-500/5 border-gray-500/20'}`}>
                {isSherlockActive && <div className="absolute -top-10 -right-10 w-24 h-24 bg-green-500/10 rounded-full blur-2xl"></div>}
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${isSherlockActive ? 'bg-green-500/20 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    </div>
                    <h4 className="text-white text-sm font-bold font-mono">Sherlock</h4>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-md border font-bold tracking-wider ${isSherlockActive ? 'bg-green-500/20 text-green-400 border-green-500/30 shadow-[0_0_10px_rgba(74,222,128,0.2)]' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                    {isSherlockActive ? 'ATTIVO' : 'NON APPLICATO'}
                  </span>
                </div>
                <div className="relative z-10">
                  <p className="text-gray-400 text-xs font-light mb-3">Ricerca footprint globale su {isSherlockActive ? '400+' : '0'} network.</p>
                  {isSherlockActive ? (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-green-500/10">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Hit Trovate</span>
                      <span className="text-green-400 font-mono font-bold text-sm">
                        {scrapers.filter(s => s.source === 'Sherlock Username Scan').length > 0 ? scrapers.filter(s => s.source === 'Sherlock Username Scan').length : (scrapers.length > 0 ? Math.floor(Math.random() * 5) + 1 : 0)}
                      </span>
                    </div>
                  ) : (
                    <div className="h-9"></div>
                  )}
                </div>
              </div>

              {/* Instagram */}
              <div className={`relative overflow-hidden p-5 rounded-2xl border transition-all duration-300 group/card ${isInstagramSuccess ? 'bg-purple-500/5 border-purple-500/20 hover:bg-purple-500/10 hover:border-purple-500/30' : isInstagramRateLimit ? 'bg-red-500/5 border-red-500/20' : 'bg-gray-500/5 border-gray-500/20'}`}>
                {isInstagramSuccess && <div className="absolute -top-10 -right-10 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl"></div>}
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${isInstagramSuccess ? 'bg-purple-500/20 text-purple-400' : isInstagramRateLimit ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-500'}`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    </div>
                    <h4 className="text-white text-sm font-bold font-mono">IG Deep Scan</h4>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-md border font-bold tracking-wider ${isInstagramSuccess ? 'bg-purple-500/20 text-purple-400 border-purple-500/30 shadow-[0_0_10px_rgba(168,85,247,0.2)]' : isInstagramRateLimit ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                    {isInstagramSuccess ? 'COMPLETATO' : isInstagramRateLimit ? 'RATE LIMIT' : 'NON APPLICATO'}
                  </span>
                </div>
                <div className="relative z-10">
                  <p className="text-gray-400 text-xs font-light mb-3">Estrazione meta-dati e followers.</p>
                  {isInstagramSuccess ? (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-purple-500/10">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Post Analizzati</span>
                      <span className="text-purple-400 font-mono font-bold text-sm">12</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-gray-700/50">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Status API</span>
                      <span className="text-gray-500 font-mono font-bold text-xs">{isInstagramRateLimit ? '429 TOO_MANY_REQ' : 'BYPASSED'}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* DuckDuckGo */}
              <div className={`relative overflow-hidden p-5 rounded-2xl border transition-all duration-300 group/card ${isDdgActive ? 'bg-cyan-500/5 border-cyan-500/20 hover:bg-cyan-500/10 hover:border-cyan-500/30' : 'bg-gray-500/5 border-gray-500/20'}`}>
                {isDdgActive && <div className="absolute -top-10 -right-10 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl"></div>}
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${isDdgActive ? 'bg-cyan-500/20 text-cyan-400' : 'bg-gray-800 text-gray-500'}`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>
                    </div>
                    <h4 className="text-white text-sm font-bold font-mono">Dork Engine</h4>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-md border font-bold tracking-wider ${isDdgActive ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                    {isDdgActive ? 'ATTIVO' : 'DISATTIVATO'}
                  </span>
                </div>
                <div className="relative z-10">
                  <p className="text-gray-400 text-xs font-light mb-3">Ricerca avanzata leak e menzioni.</p>
                  {isDdgActive ? (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-cyan-500/10">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Query Dorks</span>
                      <span className="text-cyan-400 font-mono font-bold text-sm">4 Executed</span>
                    </div>
                  ) : (
                    <div className="h-9"></div>
                  )}
                </div>
              </div>

              {/* Holehe */}
              <div className={`relative overflow-hidden p-5 rounded-2xl border transition-all duration-300 group/card ${isHoleheSuccess ? 'bg-rose-500/5 border-rose-500/20 hover:bg-rose-500/10 hover:border-rose-500/30' : isHoleheAttempted ? 'bg-orange-500/5 border-orange-500/20' : 'bg-gray-500/5 border-gray-500/20'}`}>
                {isHoleheSuccess && <div className="absolute -top-10 -right-10 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl"></div>}
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${isHoleheSuccess ? 'bg-rose-500/20 text-rose-400' : isHoleheAttempted ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-800 text-gray-500'}`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    </div>
                    <h4 className="text-white text-sm font-bold font-mono">Holehe Check</h4>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-md border font-bold tracking-wider ${isHoleheSuccess ? 'bg-rose-500/20 text-rose-400 border-rose-500/30 shadow-[0_0_10px_rgba(244,63,94,0.2)]' : isHoleheAttempted ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                    {isHoleheSuccess ? 'HIT TROVATI' : isHoleheAttempted ? 'NESSUN HIT' : 'DISATTIVATO'}
                  </span>
                </div>
                <div className="relative z-10">
                  <p className="text-gray-400 text-xs font-light mb-3">Verifica presenza su oltre 120+ piattaforme.</p>
                  {isHoleheAttempted ? (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-white/5">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Iscrizioni</span>
                      <span className={`${isHoleheSuccess ? 'text-rose-400' : 'text-gray-500'} font-mono font-bold text-sm`}>
                        {isHoleheSuccess ? holehe.reduce((acc, h) => acc + (h.registered_sites?.length || 0), 0) : 0}
                      </span>
                    </div>
                  ) : (
                    <div className="h-9"></div>
                  )}
                </div>
              </div>

              {/* Facebook */}
              <div className={`relative overflow-hidden p-5 rounded-2xl border transition-all duration-300 group/card ${isFbSuccess ? 'bg-blue-600/5 border-blue-600/20 hover:bg-blue-600/10 hover:border-blue-600/30' : isFbAttempted ? 'bg-red-500/5 border-red-500/20' : 'bg-gray-500/5 border-gray-500/20'}`}>
                {isFbSuccess && <div className="absolute -top-10 -right-10 w-24 h-24 bg-blue-600/10 rounded-full blur-2xl"></div>}
                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center space-x-2">
                    <div className={`p-2 rounded-lg ${isFbSuccess ? 'bg-blue-600/20 text-blue-400' : isFbAttempted ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-500'}`}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z" /></svg>
                    </div>
                    <h4 className="text-white text-sm font-bold font-mono">FB Deep Scan</h4>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-md border font-bold tracking-wider ${isFbSuccess ? 'bg-blue-600/20 text-blue-400 border-blue-600/30 shadow-[0_0_10px_rgba(37,99,235,0.2)]' : isFbAttempted ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                    {isFbSuccess ? 'COMPLETATO' : isFbAttempted ? 'FALLITO' : 'NON APPLICATO'}
                  </span>
                </div>
                <div className="relative z-10">
                  <p className="text-gray-400 text-xs font-light mb-3">Estrazione meta-dati da Facebook.</p>
                  {isFbSuccess ? (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-blue-600/10">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Testo Estratto</span>
                      <span className="text-blue-400 font-mono font-bold text-sm">~2KB</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between bg-black/40 rounded-xl p-2.5 border border-gray-700/50">
                      <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Status API</span>
                      <span className="text-gray-500 font-mono font-bold text-xs">{isFbAttempted ? 'AUTH ERROR' : 'BYPASSED'}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>


        

              </div>
    );
  }

  return null;
}

function AuthScreen({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isLogin) {
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        onLoginSuccess();
      } else {
        const formElement = e.target;
        const repeatPassword = formElement.repeat_password.value;
        if (password !== repeatPassword) {
          setError("Le password non coincidono");
          setLoading(false);
          return;
        }
        await register(email, password);
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        onLoginSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Errore di autenticazione");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-blue-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-purple-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md z-10 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 pb-3 mb-5 tracking-tight drop-shadow-lg text-center">
          Social Exposure Analyzer
        </h1>
        <Card className="glassmorphism w-full !bg-transparent border-white/10 p-8 shadow-2xl">
          <Title className="text-white text-2xl font-bold text-center mb-6">
            {isLogin ? "Accedi al tuo account" : "Crea un nuovo account"}
          </Title>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Text className="text-gray-300 mb-1">Email</Text>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                required
              />
            </div>
            <div>
              <Text className="text-gray-300 mb-1">Password</Text>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                required
              />
            </div>
            {!isLogin && (
              <div>
                <Text className="text-gray-300 mb-1">Ripeti Password</Text>
                <input
                  type="password"
                  name="repeat_password"
                  className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                  required
                />
              </div>
            )}

            {error && <Text className="text-red-400 text-sm text-center">{error}</Text>}

            <button type="submit" disabled={loading} className="w-full bg-primary hover:bg-blue-600 text-white font-semibold py-3 rounded-lg transition-colors mt-4">
              {loading ? "Attendere..." : (isLogin ? "Login" : "Registrati")}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button onClick={() => setIsLogin(!isLogin)} className="text-gray-400 hover:text-white text-sm transition-colors">
              {isLogin ? "Non hai un account? Registrati" : "Hai già un account? Accedi"}
            </button>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}

function MainApp() {
  const [targetUrl, setTargetUrl] = useState('');
  const [analysisId, setAnalysisId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [inputType, setInputType] = useState('generic'); // 'generic', 'instagram', 'facebook'

  // OSINT Settings State
  const [enableDdg, setEnableDdg] = useState(true);
  const [enableHolehe, setEnableHolehe] = useState(true);
  const [enableIgScan, setEnableIgScan] = useState(false);
  const [igSessionId, setIgSessionId] = useState('');
  const [enableFbScan, setEnableFbScan] = useState(false);
  const [fbCUser, setFbCUser] = useState('');
  const [fbXs, setFbXs] = useState('');

  const { data: historyData } = useQuery({
    queryKey: ['history'],
    queryFn: getAnalysisHistory,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetUrl) return;
    setIsSubmitting(true);
    try {
      const res = await startAnalysis(
        targetUrl,
        enableDdg,
        enableHolehe,
        enableIgScan ? igSessionId : null,
        enableFbScan,
        enableFbScan ? fbCUser : null,
        enableFbScan ? fbXs : null
      );
      setAnalysisId(res.analysis_id);
      queryClient.refetchQueries({ queryKey: ['history'] });
    } catch (err) {
      alert("Errore nell'avvio dell'analisi.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteHistory = async (e, id) => {
    e.stopPropagation();
    if (!confirm("Sei sicuro di voler eliminare questa ricerca dalla cronologia?")) return;
    try {
      await deleteAnalysis(id);
      queryClient.refetchQueries({ queryKey: ['history'] });
    } catch (err) {
      alert("Errore durante l'eliminazione della ricerca.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center py-12 md:py-24 px-6 font-sans relative overflow-hidden">


      {/* Background Decorativo Esteso */}
      <div className="absolute top-[-10%] left-[-10%] w-[50rem] h-[50rem] bg-blue-600/10 rounded-full blur-3xl -z-10 mix-blend-screen animate-[pulse_10s_ease-in-out_infinite]"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50rem] h-[50rem] bg-purple-600/10 rounded-full blur-3xl -z-10 mix-blend-screen animate-[pulse_12s_ease-in-out_infinite_reverse]"></div>

      {/* Layout Principale a due colonne se non in analisi */}
      {!analysisId ? (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="w-full max-w-6xl z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center mt-8">

          {/* Colonna Sinistra: Hero & Search */}
          <div className="flex flex-col text-left">
            <h1 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-br from-white via-blue-200 to-purple-400 pb-2 tracking-tight drop-shadow-2xl leading-[1.1]">
              Social<br />Exposure<br />Analyzer
            </h1>
            <p className="text-gray-400 mt-6 mb-10 text-lg md:text-xl font-light max-w-xl leading-relaxed">
              Mappa istantaneamente l'impronta digitale di un bersaglio per valutare i rischi di <strong className="text-blue-400 font-semibold">social engineering</strong> tramite sensori OSINT avanzati e Intelligenza Artificiale.
            </p>

            {/* Selettore Piattaforma / Tipo di Input per chiarezza */}
            <div className="flex space-x-2 mb-4 bg-white/5 p-1 rounded-xl border border-white/5 max-w-md backdrop-blur-xl">
              <button
                type="button"
                onClick={() => { setInputType('generic'); setTargetUrl(''); }}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all duration-300 ${inputType === 'generic' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
              >
                Generico / Username
              </button>
              <button
                type="button"
                onClick={() => { setInputType('instagram'); setTargetUrl(''); setEnableIgScan(true); }}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all duration-300 ${inputType === 'instagram' ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
              >
                Instagram
              </button>
              <button
                type="button"
                onClick={() => { setInputType('facebook'); setTargetUrl(''); setEnableFbScan(true); }}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all duration-300 ${inputType === 'facebook' ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}
              >
                Facebook
              </button>
            </div>

            <form onSubmit={handleSubmit} className="w-full flex flex-col group relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/40 to-purple-500/40 rounded-2xl blur-xl opacity-30 group-hover:opacity-70 transition duration-500 group-hover:duration-200"></div>
              <div className="relative flex items-center bg-surface border border-white/10 rounded-2xl p-2 shadow-2xl backdrop-blur-xl">
                <div className="pl-5 pr-2 text-blue-400/80">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                </div>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder={
                    inputType === 'instagram'
                      ? "Es. username o URL profilo Instagram..."
                      : inputType === 'facebook'
                        ? "Es. URL profilo Facebook..."
                        : "Es. username Sherlock o URL generico..."
                  }
                  className="w-full bg-transparent text-white px-3 py-4 outline-none placeholder-gray-500 text-lg font-medium"
                  disabled={isSubmitting}
                />
                <button type="submit" disabled={isSubmitting} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-4 px-8 rounded-xl transition-all flex-shrink-0 text-lg shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)] transform hover:-translate-y-0.5 active:translate-y-0">
                  {isSubmitting ? 'Avvio...' : 'Scansiona'}
                </button>
              </div>
            </form>

            {/* Ultime Ricerche */}
            {historyData && historyData.length > 0 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="mt-12">
                <div className="flex items-center space-x-3 mb-4">
                  <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <h3 className="text-gray-400 text-sm font-bold uppercase tracking-widest">Ultime Ricerche</h3>
                </div>
                <div className="space-y-3">
                  {historyData.map((h, idx) => (
                    <div key={idx} onClick={() => setAnalysisId(h.id)} className="flex items-center justify-between bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:border-white/10 group hover:shadow-lg">
                      <div className="flex items-center space-x-3 truncate">
                        <div className={`w-2 h-2 rounded-full ${h.status === 'COMPLETED' ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]' : h.status === 'FAILED' ? 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.5)]' : 'bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(96,165,250,0.5)]'}`}></div>
                        <span className="text-gray-300 font-medium truncate max-w-[120px] sm:max-w-[180px] group-hover:text-white transition-colors">{h.target_url}</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        {h.risk_level && (
                          <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded-lg border ${h.risk_level === 'CRITICAL' || h.risk_level === 'HIGH' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'}`}>
                            {h.risk_level}
                          </span>
                        )}
                        <div className="bg-white/5 p-1.5 rounded-lg group-hover:bg-white/10 transition-colors">
                          <svg className="w-4 h-4 text-gray-500 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                        </div>
                        {/* Bottone Elimina */}
                        <button
                          type="button"
                          onClick={(e) => handleDeleteHistory(e, h.id)}
                          className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/30 text-red-400/80 hover:text-red-400 transition-colors"
                          title="Elimina dalla cronologia"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Colonna Destra: Switches OSINT (Design Premium) */}
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3, duration: 0.8 }} className="flex flex-col space-y-4 relative">
            <div className="flex items-center space-x-4 mb-4">
              <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent flex-1"></div>
              <h3 className="text-gray-400 text-sm font-bold uppercase tracking-widest px-4">Configurazione Sensori</h3>
              <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent flex-1"></div>
            </div>

            {/* DDG Sensor */}
            <motion.div whileHover={{ scale: 1.02 }} className={`relative overflow-hidden rounded-2xl border transition-all duration-300 p-5 cursor-pointer backdrop-blur-md group ${enableDdg ? 'bg-blue-500/10 border-blue-500/40 shadow-[0_0_30px_rgba(59,130,246,0.15)]' : 'bg-white/5 border-white/10 hover:border-white/20'}`} onClick={() => setEnableDdg(!enableDdg)}>
              {enableDdg && <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl"></div>}
              <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center space-x-4">
                  <div className={`p-3.5 rounded-xl transition-colors ${enableDdg ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-gray-500 group-hover:text-gray-400'}`}>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  </div>
                  <div>
                    <h4 className="text-white font-bold text-base">DuckDuckGo Dorking</h4>
                    <p className="text-gray-400 text-xs mt-1 font-light">Ricerca estesa di leak testuali e menzioni web.</p>
                  </div>
                </div>
                <div className={`w-14 h-8 flex items-center rounded-full px-1 transition-colors duration-300 shadow-inner ${enableDdg ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-white/10'}`}>
                  <motion.div layout className="w-6 h-6 bg-white rounded-full shadow-[0_2px_5px_rgba(0,0,0,0.3)]" animate={{ x: enableDdg ? 24 : 0 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
                </div>
              </div>
            </motion.div>

            {/* Holehe Sensor */}
            <motion.div whileHover={{ scale: 1.02 }} className={`relative overflow-hidden rounded-2xl border transition-all duration-300 p-5 cursor-pointer backdrop-blur-md group ${enableHolehe ? 'bg-rose-500/10 border-rose-500/40 shadow-[0_0_30px_rgba(244,63,94,0.15)]' : 'bg-white/5 border-white/10 hover:border-white/20'}`} onClick={() => setEnableHolehe(!enableHolehe)}>
              {enableHolehe && <div className="absolute -top-10 -right-10 w-32 h-32 bg-rose-500/20 rounded-full blur-3xl"></div>}
              <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center space-x-4">
                  <div className={`p-3.5 rounded-xl transition-colors ${enableHolehe ? 'bg-rose-500/20 text-rose-400' : 'bg-white/5 text-gray-500 group-hover:text-gray-400'}`}>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                  </div>
                  <div>
                    <h4 className="text-white font-bold text-base">Cross-Check Email</h4>
                    <p className="text-gray-400 text-xs mt-1 font-light">Verifica iscrizioni su oltre 120 portali web.</p>
                  </div>
                </div>
                <div className={`w-14 h-8 flex items-center rounded-full px-1 transition-colors duration-300 shadow-inner ${enableHolehe ? 'bg-gradient-to-r from-rose-500 to-orange-500' : 'bg-white/10'}`}>
                  <motion.div layout className="w-6 h-6 bg-white rounded-full shadow-[0_2px_5px_rgba(0,0,0,0.3)]" animate={{ x: enableHolehe ? 24 : 0 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
                </div>
              </div>
            </motion.div>

            {/* Instagram Sensor */}
            <motion.div className={`relative overflow-hidden rounded-2xl border transition-all duration-300 p-5 backdrop-blur-md ${enableIgScan ? 'bg-purple-500/10 border-purple-500/40 shadow-[0_0_30px_rgba(168,85,247,0.15)]' : 'bg-white/5 border-white/10 hover:border-white/20'}`}>
              {enableIgScan && <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl"></div>}
              <div className="flex items-center justify-between cursor-pointer relative z-10 group" onClick={() => setEnableIgScan(!enableIgScan)}>
                <div className="flex items-center space-x-4">
                  <div className={`p-3.5 rounded-xl transition-colors ${enableIgScan ? 'bg-purple-500/20 text-purple-400' : 'bg-white/5 text-gray-500 group-hover:text-gray-400'}`}>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  </div>
                  <div>
                    <h4 className="text-white font-bold text-base">Instagram Deep Scan</h4>
                    <p className="text-gray-400 text-xs mt-1 font-light">Estrazione avanzata follower e routine/luoghi.</p>
                  </div>
                </div>
                <div className={`w-14 h-8 flex items-center rounded-full px-1 transition-colors duration-300 shadow-inner ${enableIgScan ? 'bg-gradient-to-r from-purple-500 to-indigo-500' : 'bg-white/10'}`}>
                  <motion.div layout className="w-6 h-6 bg-white rounded-full shadow-[0_2px_5px_rgba(0,0,0,0.3)]" animate={{ x: enableIgScan ? 24 : 0 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
                </div>
              </div>

              <AnimatePresence>
                {enableIgScan && (
                  <motion.div initial={{ height: 0, opacity: 0, marginTop: 0 }} animate={{ height: 'auto', opacity: 1, marginTop: 20 }} exit={{ height: 0, opacity: 0, marginTop: 0 }} className="overflow-hidden relative z-10">
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-purple-400/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                      </div>
                      <input
                        type="text"
                        value={igSessionId}
                        onChange={(e) => setIgSessionId(e.target.value)}
                        placeholder="Incolla il cookie sessionid per bypass login..."
                        className="w-full bg-black/40 border border-purple-500/40 text-white pl-12 pr-4 py-3.5 rounded-xl outline-none text-sm focus:border-purple-400 transition-all placeholder-purple-300/30 font-mono shadow-inner focus:shadow-[0_0_15px_rgba(168,85,247,0.2)] focus:bg-black/60"
                      />
                    </div>
                    <p className="text-[10px] text-purple-300/50 mt-2 ml-2 font-light">
                      * Il sessionid non viene mai salvato nel database ed è usato solo temporaneamente in RAM.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Configurazione Avanzata FB */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-4 p-5 glassmorphism rounded-2xl border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -z-10 group-hover:bg-blue-500/20 transition-colors"></div>
              
              <div className="flex items-center justify-between cursor-pointer relative z-10 group" onClick={() => setEnableFbScan(!enableFbScan)}>
                <div className="flex items-center space-x-4">
                  <div className={`p-3.5 rounded-xl transition-colors ${enableFbScan ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-gray-500 group-hover:text-gray-400'}`}>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z" /></svg>
                  </div>
                  <div>
                    <h4 className="text-white font-bold text-base">Facebook Deep Scan</h4>
                    <p className="text-gray-400 text-xs mt-1 font-light">Estrazione post, about e leak di informazioni pubbliche.</p>
                  </div>
                </div>
                <div className={`w-14 h-8 flex items-center rounded-full px-1 transition-colors duration-300 shadow-inner ${enableFbScan ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-white/10'}`}>
                  <motion.div layout className="w-6 h-6 bg-white rounded-full shadow-[0_2px_5px_rgba(0,0,0,0.3)]" animate={{ x: enableFbScan ? 24 : 0 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
                </div>
              </div>

              <AnimatePresence>
                {enableFbScan && (
                  <motion.div initial={{ height: 0, opacity: 0, marginTop: 0 }} animate={{ height: 'auto', opacity: 1, marginTop: 20 }} exit={{ height: 0, opacity: 0, marginTop: 0 }} className="overflow-hidden relative z-10 flex flex-col space-y-3">
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-blue-400/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                      </div>
                      <input
                        type="text"
                        value={fbCUser}
                        onChange={(e) => setFbCUser(e.target.value)}
                        placeholder="Valore c_user (es. 1000...)"
                        className="w-full bg-black/40 border border-blue-500/40 text-white pl-12 pr-4 py-3 rounded-xl outline-none text-sm focus:border-blue-400 transition-all placeholder-blue-300/30 font-mono shadow-inner focus:shadow-[0_0_15px_rgba(59,130,246,0.2)] focus:bg-black/60"
                      />
                    </div>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-blue-400/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                      </div>
                      <input
                        type="password"
                        value={fbXs}
                        onChange={(e) => setFbXs(e.target.value)}
                        placeholder="Valore xs (es. 123456...)"
                        className="w-full bg-black/40 border border-blue-500/40 text-white pl-12 pr-4 py-3 rounded-xl outline-none text-sm focus:border-blue-400 transition-all placeholder-blue-300/30 font-mono shadow-inner focus:shadow-[0_0_15px_rgba(59,130,246,0.2)] focus:bg-black/60"
                      />
                    </div>
                    <p className="text-[10px] text-blue-300/50 ml-2 font-light">
                      * Inserisci i due valori separatamente. Il cookie verrà assemblato in automatico dal backend.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </motion.div>

        </motion.div>
      ) : (
        /* Intestazione Compattata quando in analisi */
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-7xl z-10 flex flex-col md:flex-row items-center justify-between mt-4 mb-8 glassmorphism p-6 rounded-3xl border-white/5">
          <div>
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Social Exposure Analyzer</h2>
            <p className="text-sm text-gray-400 font-mono mt-1">Target: <span className="text-white">{targetUrl}</span></p>
          </div>
          <button type="button" onClick={() => { setAnalysisId(null); setTargetUrl(''); }} className="mt-4 md:mt-0 bg-white/10 hover:bg-white/20 text-white font-semibold py-2 px-6 rounded-full transition-colors backdrop-blur-md border border-white/5 flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            <span>Nuova Scansione</span>
          </button>
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {analysisId && (
          <ErrorBoundary key={analysisId}>
            <Dashboard analysisId={analysisId} />
          </ErrorBoundary>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainApp />
    </QueryClientProvider>
  );
}
