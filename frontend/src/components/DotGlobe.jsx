import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const DOT_COUNT = 1700;

const DotGlobe = () => {
    const containerRef = useRef(null);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return undefined;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
        camera.position.z = 4.1;
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        const globe = new THREE.Group();
        scene.add(globe);
        const positions = new Float32Array(DOT_COUNT * 3);
        const colors = new Float32Array(DOT_COUNT * 3);
        const green = new THREE.Color('#8ee4ba');
        const mint = new THREE.Color('#d5ffe6');
        const coral = new THREE.Color('#ffad9b');

        for (let index = 0; index < DOT_COUNT; index += 1) {
            const y = 1 - (index / (DOT_COUNT - 1)) * 2;
            const radius = Math.sqrt(1 - y * y);
            const theta = Math.PI * (3 - Math.sqrt(5)) * index;
            positions[index * 3] = Math.cos(theta) * radius;
            positions[index * 3 + 1] = y;
            positions[index * 3 + 2] = Math.sin(theta) * radius;
            const color = Math.sin(theta * 3) * y > 0.45 ? coral : y > 0.2 ? mint : green;
            colors[index * 3] = color.r;
            colors[index * 3 + 1] = color.g;
            colors[index * 3 + 2] = color.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        const material = new THREE.PointsMaterial({ size: 0.026, vertexColors: true, transparent: true, opacity: 0.96, sizeAttenuation: true });
        globe.add(new THREE.Points(geometry, material));

        const rings = new THREE.Group();
        [1.16, 1.34].forEach((radius, index) => {
            const ring = new THREE.Mesh(
                new THREE.TorusGeometry(radius, 0.006, 8, 160),
                new THREE.MeshBasicMaterial({ color: index ? '#ffad9b' : '#8ee4ba', transparent: true, opacity: 0.5 })
            );
            ring.rotation.x = Math.PI / 2.8 + index * 0.3;
            ring.rotation.y = index ? Math.PI / 4 : -Math.PI / 6;
            rings.add(ring);
        });
        globe.add(rings);

        let dragging = false;
        let previousX = 0;
        let previousY = 0;
        let rotationX = 0.2;
        let rotationY = -0.5;
        const onPointerDown = (event) => { dragging = true; previousX = event.clientX; previousY = event.clientY; container.setPointerCapture?.(event.pointerId); };
        const onPointerMove = (event) => {
            if (!dragging) return;
            rotationY += (event.clientX - previousX) * 0.008;
            rotationX += (event.clientY - previousY) * 0.006;
            previousX = event.clientX;
            previousY = event.clientY;
        };
        const onPointerUp = () => { dragging = false; };
        container.addEventListener('pointerdown', onPointerDown);
        container.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);

        const resize = () => {
            const size = Math.min(container.clientWidth, container.clientHeight);
            renderer.setSize(size, size, false);
            camera.updateProjectionMatrix();
        };
        const resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(container);
        resize();

        let frame;
        const animate = () => {
            frame = requestAnimationFrame(animate);
            if (!dragging) rotationY += 0.0022;
            globe.rotation.x = rotationX;
            globe.rotation.y = rotationY;
            rings.rotation.z += 0.0014;
            renderer.render(scene, camera);
        };
        animate();

        return () => {
            cancelAnimationFrame(frame);
            resizeObserver.disconnect();
            container.removeEventListener('pointerdown', onPointerDown);
            container.removeEventListener('pointermove', onPointerMove);
            window.removeEventListener('pointerup', onPointerUp);
            geometry.dispose();
            material.dispose();
            renderer.dispose();
            renderer.domElement.remove();
        };
    }, []);

    return <div ref={containerRef} className="dot-globe" aria-label="Interactive satellite coverage globe. Drag to rotate." role="img" />;
};

export default DotGlobe;
