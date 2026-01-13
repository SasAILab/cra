"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

// Dynamically import ForceGraph2D as it relies on window/canvas
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  ),
});

interface KnowledgeGraphProps {
  data: {
    nodes: any[];
    links: any[];
  } | null;
  width?: number;
  height?: number;
}

export default function KnowledgeGraph({ data, width, height }: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoverNode, setHoverNode] = useState<any | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());

  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: any;
  }>({ visible: false, x: 0, y: 0, content: null });

  // Update highlight sets when hoverNode changes
  useEffect(() => {
    const newHighlightNodes = new Set();
    const newHighlightLinks = new Set();

    if (hoverNode && data?.links) {
      newHighlightNodes.add(hoverNode.id);
      data.links.forEach((link: any) => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        
        if (sourceId === hoverNode.id || targetId === hoverNode.id) {
          newHighlightLinks.add(link);
          newHighlightNodes.add(sourceId);
          newHighlightNodes.add(targetId);
        }
      });
    }

    setHighlightNodes(newHighlightNodes);
    setHighlightLinks(newHighlightLinks);
  }, [hoverNode, data]);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });
    }
  }, []);

  useEffect(() => {
    if (fgRef.current) {
      // Configure simulation forces to spread nodes out
      const fg = fgRef.current;
      
      // Increase repulsion to push nodes apart (default is usually around -30)
      fg.d3Force('charge').strength(-200).distanceMax(500);
      
      // Increase link distance
      fg.d3Force('link').distance(80);

      // Re-heat simulation
      fg.d3ReheatSimulation();
    }
  }, [data]);

  const handleNodeHover = useCallback((node: any) => {
    setHoverNode(node || null);
    
    if (node && fgRef.current) {
      const { x, y } = fgRef.current.graph2ScreenCoords(node.x, node.y);
      setTooltip({
        visible: true,
        x: x,
        y: y,
        content: {
          title: node.label,
          type: node.entity_type,
          desc: node.desc
        }
      });
      if (containerRef.current) containerRef.current.style.cursor = 'pointer';
    } else {
      setTooltip(prev => ({ ...prev, visible: false }));
      if (containerRef.current) containerRef.current.style.cursor = 'default';
    }
  }, []);

  const handleLinkHover = useCallback((link: any) => {
    if (link && fgRef.current) {
      const start = link.source;
      const end = link.target;
      if (typeof start === 'object' && typeof end === 'object') {
        const midX = start.x + (end.x - start.x) / 2;
        const midY = start.y + (end.y - start.y) / 2;
        const { x, y } = fgRef.current.graph2ScreenCoords(midX, midY);
        setTooltip({
          visible: true,
          x: x,
          y: y,
          content: {
            title: link.label,
            type: 'RELATIONSHIP',
            desc: link.desc
          }
        });
        if (containerRef.current) containerRef.current.style.cursor = 'pointer';
      }
    } else {
      setTooltip(prev => ({ ...prev, visible: false }));
      if (containerRef.current) containerRef.current.style.cursor = 'default';
    }
  }, []);

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground bg-muted/10">
        No Knowledge Graph data available
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[400px] border rounded-md overflow-hidden bg-slate-50 dark:bg-slate-950">
      <ForceGraph2D
        ref={fgRef}
        width={width || dimensions.width}
        height={height || dimensions.height}
        graphData={data}
        onNodeHover={handleNodeHover}
        onLinkHover={handleLinkHover}
        nodeColor={node => (node as any).color || "#3b82f6"}
        linkColor={link => hoverNode && !highlightLinks.has(link) ? "#e2e8f0" : "#94a3b8"}
        linkWidth={link => hoverNode && highlightLinks.has(link) ? 2 : 1}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleWidth={2}
        linkCurvature={0.2}
        nodeRelSize={6}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        cooldownTicks={200}
        onNodeDragEnd={node => {
          node.fx = node.x;
          node.fy = node.y;
        }}
        nodeCanvasObjectMode={() => 'after'}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const isHovered = hoverNode && node.id === hoverNode.id;
          const isNeighbor = hoverNode && highlightNodes.has(node.id);
          const isDimmed = hoverNode && !isHovered && !isNeighbor;

          const label = node.label;
          const fontSize = isHovered ? 12/globalScale : 10/globalScale;
          
          // Draw Node Circle
          const r = 6; 
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
          
          // Dimming effect
          ctx.globalAlpha = isDimmed ? 0.2 : 1;
          
          ctx.fillStyle = node.color || "#3b82f6";
          
          // Glow effect for active nodes
          if (isHovered || isNeighbor) {
             ctx.shadowColor = node.color || "#3b82f6";
             ctx.shadowBlur = isHovered ? 20 : 10;
          } else {
             ctx.shadowBlur = 0;
          }
          
          ctx.fill();
          
          // White border
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5 / globalScale;
          ctx.stroke();
          
          // Reset context
          ctx.shadowBlur = 0;
          
          // Label Rendering
          if (!label) return;
          
          // Skip label if dimmed, unless it's a very important node (optional, for now hide to clean up)
          // Actually, let's keep labels but very faint if dimmed
          if (isDimmed) ctx.globalAlpha = 0.1;

          ctx.font = `${isHovered ? 'bold ' : ''}${fontSize}px Sans-Serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          
          const yPos = node.y + r + 2;

          // Draw text background for readability
          const textWidth = ctx.measureText(label).width;
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);
          
          // Background
          ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'; 
          if (isDimmed) ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
          
          ctx.fillRect(node.x - bckgDimensions[0] / 2, yPos - 1, bckgDimensions[0], bckgDimensions[1]);

          // Text
          ctx.fillStyle = '#0f172a';
          ctx.fillText(label, node.x, yPos);
          
          // Restore opacity
          ctx.globalAlpha = 1;
        }}
        linkCanvasObjectMode={() => 'after'}
        linkCanvasObject={(link: any, ctx, globalScale) => {
          const isDimmed = hoverNode && !highlightLinks.has(link);
          if (isDimmed) return; // Don't draw labels for dimmed links to reduce clutter

          const label = link.label;
          if (!label) return;

          const start = link.source;
          const end = link.target;
          if (typeof start !== 'object' || typeof end !== 'object') return;

          const textPos = Object.assign({}, ...['x', 'y'].map(c => ({
            [c]: start[c] + (end[c] - start[c]) / 2 
          })));

          const relLink = { x: end.x - start.x, y: end.y - start.y };
          const maxTextLength = Math.sqrt(Math.pow(relLink.x, 2) + Math.pow(relLink.y, 2)) - 10;

          const fontSize = 10/globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          
          const textWidth = ctx.measureText(label).width;
          if (textWidth > maxTextLength) return;

          ctx.save();
          ctx.translate(textPos.x, textPos.y);

          const angle = Math.atan2(relLink.y, relLink.x);
          const textAngle = (angle > Math.PI / 2 || angle < -Math.PI / 2) ? angle + Math.PI : angle;
          ctx.rotate(textAngle);

          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillRect(-bckgDimensions[0] / 2, -bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

          ctx.fillStyle = '#475569'; 
          ctx.fillText(label, 0, 0);
          ctx.restore();
        }}
      />
      {tooltip.visible && tooltip.content && typeof document !== 'undefined' && createPortal(
        <div 
          className="fixed z-[9999] p-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl pointer-events-none transition-opacity duration-200 max-w-xs"
          style={{ 
            left: tooltip.x, 
            top: tooltip.y,
            transform: 'translate(-50%, -100%) translateY(-10px)' 
          }}
        >
          <div className="font-semibold text-slate-900 dark:text-slate-100 mb-1">
            {tooltip.content.title}
          </div>
          {tooltip.content.type && (
             <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">
               {tooltip.content.type}
             </div>
          )}
          <div className="text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed text-xs">
            {tooltip.content.desc && tooltip.content.desc !== tooltip.content.title ? tooltip.content.desc : (tooltip.content.desc || "No details available")}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
