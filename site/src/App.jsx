import { motion, useScroll, useSpring } from 'framer-motion'
import Hero3D from './Hero3D.jsx'

const REPO = 'https://github.com/jayaprakash-pixel/Real-time-Visual-Identification-System'

// status is deliberately honest: built / partial / roadmap
const MODULES = [
  { n: '01', t: 'Registration & Database', s: 'partial', d: 'React frontend, Supabase persons table, photo upload. Not yet linked to the AI module.' },
  { n: '02', t: 'AI Vision & Recognition', s: 'built', d: 'Frame buffer, YuNet, SFace, tracking, quality gate, 3-of-5 verification, evidence capture.' },
  { n: '03', t: 'Intelligence & Alerts', s: 'roadmap', d: 'Only a console/beep demo exists today. The real alert service is next.' },
]
const STEPS = ['Camera', 'Latest-frame buffer', 'Detect (YuNet)', 'Track IDs', 'Embed (SFace)', 'Cosine match', '3-of-5 verify', 'Scene + alert']

const fade = { hidden: { opacity: 0, y: 30 }, show: { opacity: 1, y: 0 } }
const list = { show: { transition: { staggerChildren: 0.08 } } }
const inView = { initial: 'hidden', whileInView: 'show', viewport: { once: true } }

export default function App() {
  const { scrollYProgress } = useScroll()
  const bar = useSpring(scrollYProgress, { stiffness: 120, damping: 20 })
  return (
    <>
      <motion.div className="progress" style={{ scaleX: bar }} />
      <header className="hero">
        <Hero3D />
        <motion.div className="hero-copy" initial="hidden" animate="show" variants={list}>
          <motion.span variants={fade} className="pill">Apache-2.0 · open source</motion.span>
          <motion.h1 variants={fade}>Real-time Visual <br />Identification System</motion.h1>
          <motion.p variants={fade}>A phone is the CCTV. The laptop is the control room. Register a missing person once and the AI confirms them on live video, over several frames.</motion.p>
          <motion.a variants={fade} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }} className="btn" href={REPO}>View on GitHub</motion.a>
        </motion.div>
      </header>

      <section>
        <motion.h2 {...inView} variants={fade}>The pipeline</motion.h2>
        <motion.ol className="steps" {...inView} variants={list}>
          {STEPS.map((s, i) => (
            <motion.li key={s} variants={fade} whileHover={{ y: -6 }}><b>{i + 1}</b>{s}</motion.li>
          ))}
        </motion.ol>
      </section>

      <section>
        <motion.h2 {...inView} variants={fade}>Three modules, honest status</motion.h2>
        <motion.div className="cards" {...inView} variants={list}>
          {MODULES.map((m) => (
            <motion.article key={m.n} variants={fade} whileHover={{ rotateX: 4, rotateY: -4, scale: 1.02 }} style={{ transformPerspective: 800 }}>
              <small>{m.n}</small><h3>{m.t}</h3><p>{m.d}</p><span className={`tag ${m.s}`}>{m.s}</span>
            </motion.article>
          ))}
        </motion.div>
      </section>

      <footer>Apache-2.0 · biometric data is never committed to this repository.</footer>
    </>
  )
}
