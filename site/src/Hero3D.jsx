import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Point-cloud head that slowly turns; a scan plane sweeps it and lights the points it passes.
export default function Hero3D() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    const scene = new THREE.Scene()
    const cam = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
    cam.position.z = 6
    const r = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    r.setPixelRatio(Math.min(devicePixelRatio, 2))
    el.appendChild(r.domElement)

    const N = 2600, pos = new Float32Array(N * 3), col = new Float32Array(N * 3)
    for (let i = 0; i < N; i++) {
      const u = Math.acos(2 * Math.random() - 1), v = 2 * Math.PI * Math.random()
      pos.set([1.25 * Math.sin(u) * Math.cos(v), 1.6 * Math.cos(u), 1.25 * Math.sin(u) * Math.sin(v)], i * 3)
    }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    g.setAttribute('color', new THREE.BufferAttribute(col, 3))
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ size: 0.035, vertexColors: true }))
    scene.add(pts)

    const base = new THREE.Color('#5b4a8a'), hit = new THREE.Color('#14b8a6'), c = new THREE.Color()
    const resize = () => { const w = el.clientWidth, h = el.clientHeight; r.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix() }
    resize(); addEventListener('resize', resize)

    let raf; const t0 = performance.now()
    const tick = (now) => {
      const t = (now - t0) / 1000
      pts.rotation.y = t * 0.35
      const y = Math.sin(t * 1.2) * 1.6 // scan height
      for (let i = 0; i < N; i++) {
        const k = Math.max(0, 1 - Math.abs(pos[i * 3 + 1] - y) / 0.35)
        c.copy(base).lerp(hit, k)
        col.set([c.r, c.g, c.b], i * 3)
      }
      g.attributes.color.needsUpdate = true
      r.render(scene, cam)
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => { cancelAnimationFrame(raf); removeEventListener('resize', resize); r.dispose(); el.removeChild(r.domElement) }
  }, [])
  return <div ref={ref} className="hero3d" aria-hidden="true" />
}
