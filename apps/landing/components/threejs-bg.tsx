'use client'

import { useEffect, useRef } from 'react'

export function ThreeJSBackground() {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<any>(null)

  useEffect(() => {
    if (!containerRef.current || rendererRef.current) return

    // Load Three.js script
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
    script.async = true
    script.onload = () => {
      initScene()
    }
    document.body.appendChild(script)

    function initScene() {
      const THREE = (window as any).THREE
      if (!THREE) return

      const container = containerRef.current
      if (!container) return

      const width = window.innerWidth
      const height = window.innerHeight

      // Scene setup
      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

      renderer.setSize(width, height)
      renderer.setPixelRatio(window.devicePixelRatio)
      renderer.setClearColor(0x000000, 0)
      container.appendChild(renderer.domElement)
      rendererRef.current = renderer

      camera.position.z = 8

      // Create nodes
      const nodeGroup = new THREE.Group()
      const geometry = new THREE.SphereGeometry(0.05, 16, 16)
      const whiteMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff })
      const orangeMaterial = new THREE.MeshBasicMaterial({ color: 0xFFA500 })

      const nodes = []
      for (let i = 0; i < 40; i++) {
        const material = Math.random() > 0.8 ? orangeMaterial : whiteMaterial
        const mesh = new THREE.Mesh(geometry, material)
        mesh.position.set(
          (Math.random() - 0.5) * 10,
          (Math.random() - 0.5) * 10,
          (Math.random() - 0.5) * 10
        )
        nodeGroup.add(mesh)
        nodes.push(mesh)
      }

      // Create edges
      const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.1 })
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const distance = nodes[i].position.distanceTo(nodes[j].position)
          if (distance < 3) {
            const lineGeometry = new THREE.BufferGeometry().setFromPoints([
              nodes[i].position,
              nodes[j].position
            ])
            const line = new THREE.Line(lineGeometry, lineMaterial)
            nodeGroup.add(line)
          }
        }
      }

      scene.add(nodeGroup)

      // Animation loop
      const animate = () => {
        requestAnimationFrame(animate)
        nodeGroup.rotation.x += 0.0005
        nodeGroup.rotation.y += 0.001
        renderer.render(scene, camera)
      }

      animate()

      // Handle resize
      const handleResize = () => {
        const newWidth = window.innerWidth
        const newHeight = window.innerHeight
        camera.aspect = newWidth / newHeight
        camera.updateProjectionMatrix()
        renderer.setSize(newWidth, newHeight)
      }

      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        container.removeChild(renderer.domElement)
      }
    }

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script)
      }
    }
  }, [])

  return <div ref={containerRef} className="w-full h-full" />
}
