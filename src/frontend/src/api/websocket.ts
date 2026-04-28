import type { WSMessage } from '@/types';

export type WSMessageType =
  | 'connected'
  | 'subscribed'
  | 'unsubscribed'
  | 'pong'
  | 'status'
  | 'error'
  | 'threat.detected'
  | 'alert.created'
  | 'system.update'
  | 'detector.update';

export type WSChannel = 'threats' | 'alerts' | 'system' | 'detectors';

export interface WSClientOptions {
  url?: string;
  channels?: WSChannel[];
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private channels: Set<WSChannel> = new Set();
  private onMessageCallback?: (message: WSMessage) => void;
  private onConnectCallback?: () => void;
  private onDisconnectCallback?: () => void;
  private onErrorCallback?: (error: Event) => void;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manualClose = false;

  constructor(options: WSClientOptions = {}) {
    this.url = options.url || this.getDefaultUrl();
    this.channels = new Set(options.channels || []);
    this.onMessageCallback = options.onMessage;
    this.onConnectCallback = options.onConnect;
    this.onDisconnectCallback = options.onDisconnect;
    this.onErrorCallback = options.onError;
    this.reconnectInterval = options.reconnectInterval || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
  }

  private getDefaultUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_HOST || window.location.host;
    return `${protocol}//${host}/ws`;
  }

  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.manualClose = false;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      // 订阅频道
      if (this.channels.size > 0) {
        this.subscribe(Array.from(this.channels));
      }

      this.onConnectCallback?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        this.onMessageCallback?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      this.onDisconnectCallback?.();

      // 自动重连
      if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        this.reconnectTimer = setTimeout(() => {
          this.connect();
        }, this.reconnectInterval);
      }
    };

    this.ws.onerror = (error) => {
      this.onErrorCallback?.(error);
    };
  }

  disconnect(): void {
    this.manualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(channels: WSChannel[]): void {
    channels.forEach((channel) => this.channels.add(channel));
    this.send({ action: 'subscribe', channels });
  }

  unsubscribe(channels: WSChannel[]): void {
    channels.forEach((channel) => this.channels.delete(channel));
    this.send({ action: 'unsubscribe', channels });
  }

  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  ping(): void {
    this.send({ action: 'ping' });
  }

  getStatus(): void {
    this.send({ action: 'get_status' });
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  onConnect(callback: () => void): void {
    this.onConnectCallback = callback;
  }

  onDisconnect(callback: () => void): void {
    this.onDisconnectCallback = callback;
  }

  onMessage(callback: (message: WSMessage) => void): void {
    this.onMessageCallback = callback;
  }

  onError(callback: (error: Event) => void): void {
    this.onErrorCallback = callback;
  }
}
