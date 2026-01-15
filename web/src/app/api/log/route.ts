import { NextRequest, NextResponse } from 'next/server';
import { clientLogger } from '@/lib/logger';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { level, message, meta } = body;

    // Default to 'info' if level is not provided
    const logLevel = level || 'info';

    // Format the message to include meta info if present
    const logMessage = meta ? `${message} ${JSON.stringify(meta)}` : message;

    // Log using the clientLogger (which writes to frontend-client-*.log)
    clientLogger.log({
      level: logLevel,
      message: logMessage,
      label: 'frontend-client' // Distinguish from server logs
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to write log:', error);
    return NextResponse.json({ success: false, error: 'Failed to write log' }, { status: 500 });
  }
}
