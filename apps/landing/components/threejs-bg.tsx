'use client'

import { useEffect, useRef } from 'react'

/**
 * Three.js animated background - repository graph visualization
 * Shows nodes (files/modules) connected by edges (imports/dependencies)
 * Warm orange accent nodes mixed with white nodes
 */

export function ThreeJSBackground() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Dynamically load Three.js from CDN
    const script = document.createElement('script')
    script.src = 'https://ajax.googleapis.com/ajax/libs/threejs/r125/three.min.js'
    script.onload = () => {
      initThreeJS(containerRef.current!)
    }
    document.head.appendChild(script)

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script)
      }
    }
  }, [])

  return <div ref={containerRef} className="fixed inset-0 w-full h-full pointer-events-none" />
}

function initThreeJS(container: HTMLElement) {
  const THREE = (window as any).THREE

  const devicePixelRatio = window.devicePixelRatio || 1
  const width = container.clientWidth || window.innerWidth
  const height = container.clientHeight || window.innerHeight

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(devicePixelRatio)
  renderer.setClearColor(0x000000, 0) // Transparent
  container.appendChild(renderer.domElement)

  // Create a abstract "repository graph" - a cluster of nodes and lines
  const nodeGroup = new THREE.Group()
  const nodes = [] as THREE.Mesh[]
  const nodeCount = 40

  const geo = new THREE.SphereGeometry(0.05, 16, 16)
  const whitemat = new THREE.MeshBasicMaterial({ color: 0xffffff })
  const orangeMat = new THREE.MeshBasicMaterial({ color: 0xea580c }) // Ortho warm orange

  for (let i = 0; i < nodeCount; i++) {
    const mesh = new THREE.Mesh(geo, Math.random() > 0.8 ? orangeMat : whitemat)
    mesh.position.set(
      (Math.random() - 0.5) * 10,
      (Math.random() - 0.5) * 10,
      (Math.random() - 0.5) * 10,
    )
    nodeGroup.add(mesh)
    nodes.push(mesh)
  }

  // Connect nodes with lines
  const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.1 })
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      if (nodes[i].position.distanceTo(nodes[j].position) < 3) {
        const points = [nodes[i].position, nodes[j].position]
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points)
        const line = new THREE.Line(lineGeo, lineMat)
        nodeGroup.add(line)
      }
    }
  }

  scene.add(nodeGroup)
  camera.position.z = 8

  function animate() {
    requestAnimationFrame(animate)
    nodeGroup.rotation.y += 0.001
    nodeGroup.rotation.x += 0.0005
    renderer.render(scene, camera)
  }

  window.addEventListener('resize', () => {
    const w = container.clientWidth || window.innerWidth
    const h = container.clientHeight || window.innerHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
    renderer.setPixelRatio(devicePixelRatio)
  })

  animate()
}
