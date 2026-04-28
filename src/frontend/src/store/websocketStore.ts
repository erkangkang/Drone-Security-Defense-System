import { create } from 'zustand';
import { WebSocketClient, type WSChannel } from '@/api/websocket';
import type { WSMessage } from '@/types';

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

interface WSStore {
  connected: boolean;
  connectionStatus: ConnectionStatus;
  lastMessage: WSMessage | null;
  client: WebSocketClient | null;
  subscribers: Set<(message: WSMessage) => void>;
  init: () => void;
  destroy: () => void;
  subscribe: (channels: WSChannel[]) => void;
  unsubscribe: (channels: WSChannel[]) => void;
  addSubscriber: (cb: (message: WSMessage) => void) => void;
  removeSubscriber: (cb: (message: WSMessage) => void) => void;
}

export const useWSStore = create<WSStore>((set, get) => ({
  connected: false,
  connectionStatus: 'disconnected',
  lastMessage: null,
  client: null,
  subscribers: new Set(),

  init: () => {
    const existing = get().client;
    if (existing) return;

    const client = new WebSocketClient({
      channels: ['system', 'alerts', 'threats', 'detectors'],
      onMessage: (message) => {
        set({ lastMessage: message });
        get().subscribers.forEach((cb) => cb(message));
      },
      onConnect: () => {
        set({ connected: true, connectionStatus: 'connected' });
      },
      onDisconnect: () => {
        set({ connected: false, connectionStatus: 'disconnected' });
      },
      onError: () => {
        set({ connectionStatus: 'disconnected' });
      },
    });

    client.connect();
    set({ client, connectionStatus: 'connecting' });
  },

  destroy: () => {
    const { client } = get();
    client?.disconnect();
    set({ client: null, connected: false, connectionStatus: 'disconnected' });
  },

  subscribe: (channels) => {
    get().client?.subscribe(channels);
  },

  unsubscribe: (channels) => {
    get().client?.unsubscribe(channels);
  },

  addSubscriber: (cb) => {
    const subs = new Set(get().subscribers);
    subs.add(cb);
    set({ subscribers: subs });
  },

  removeSubscriber: (cb) => {
    const subs = new Set(get().subscribers);
    subs.delete(cb);
    set({ subscribers: subs });
  },
}));
