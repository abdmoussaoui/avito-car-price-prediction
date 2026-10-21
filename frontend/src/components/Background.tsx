import React, { useEffect, useRef } from "react";

const Background: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;

    const shapes: Array<{
      x: number;
      y: number;
      size: number;
      rotation: number;
      speed: number;
      type: "square" | "triangle" | "circle";
      color: string;
    }> = [];

    const colors = [
      "rgba(99, 102, 241, 0.15)", // Indigo
      "rgba(79, 70, 229, 0.15)", // Deep indigo
      "rgba(67, 56, 202, 0.15)", // Rich indigo
      "rgba(147, 51, 234, 0.15)", // Purple
    ];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      shapes.length = 0;
      initShapes();
    };

    const initShapes = () => {
      const numberOfShapes = Math.floor(
        (window.innerWidth * window.innerHeight) / 25000
      );

      for (let i = 0; i < numberOfShapes; i++) {
        shapes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 30 + 20,
          rotation: Math.random() * Math.PI * 2,
          speed: Math.random() * 0.001 + 0.0005,
          type: ["square", "triangle", "circle"][
            Math.floor(Math.random() * 3)
          ] as any,
          color: colors[Math.floor(Math.random() * colors.length)],
        });
      }
    };

    const drawShape = (shape: (typeof shapes)[0]) => {
      ctx.save();
      ctx.translate(shape.x, shape.y);
      ctx.rotate(shape.rotation);
      ctx.fillStyle = shape.color;

      switch (shape.type) {
        case "square":
          ctx.fillRect(
            -shape.size / 2,
            -shape.size / 2,
            shape.size,
            shape.size
          );
          break;
        case "triangle":
          ctx.beginPath();
          ctx.moveTo(-shape.size / 2, shape.size / 2);
          ctx.lineTo(shape.size / 2, shape.size / 2);
          ctx.lineTo(0, -shape.size / 2);
          ctx.closePath();
          ctx.fill();
          break;
        case "circle":
          ctx.beginPath();
          ctx.arc(0, 0, shape.size / 2, 0, Math.PI * 2);
          ctx.fill();
          break;
      }

      ctx.restore();
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      shapes.forEach((shape) => {
        shape.rotation += shape.speed;
        drawShape(shape);
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    window.addEventListener("resize", resize);
    resize();
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed top-0 left-0 w-full h-full -z-10 bg-gradient-to-br from-gray-900 via-gray-800 to-black"
    />
  );
};

export default Background;
