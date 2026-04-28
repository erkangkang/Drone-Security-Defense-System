import { useEffect, useState } from 'react';
import { useWSStore } from '@/store/websocketStore';
import type { WSMessage } from '@/types';

export function useWebSocket() {
  const { lastMessage, connected, connectionStatus, addSubscriber, removeSubscriber } = useWSStore();
  const [localMessage, setLocalMessage] = useState<WSMessage | null>(null);

  useEffect(() => {
    const cb = (msg: WSMessage) => setLocalMessage(msg);
    addSubscriber(cb);
    return () => removeSubscriber(cb);
  }, [addSubscriber, removeSubscriber]);

  return {
    lastMessage: localMessage || lastMessage,
    connected,
    connectionStatus,
  };
}

export function useSystemWebSocket() {
  const { connected, addSubscriber, removeSubscriber } = useWSStore();
  const [systemUpdate, setSystemUpdate] = useState<WSMessage | null>(null);
  const [alertUpdate, setAlertUpdate] = useState<WSMessage | null>(null);
  const [threatUpdate, setThreatUpdate] = useState<WSMessage | null>(null);
  const [detectorUpdate, setDetectorUpdate] = useState<WSMessage | null>(null);

  useEffect(() => {
    const cb = (msg: WSMessage) => {
      switch (msg.type) {
        case 'system.update':
          setSystemUpdate(msg);
          break;
        case 'alert.created':
          setAlertUpdate(msg);
          break;
        case 'threat.detected':
          setThreatUpdate(msg);
          break;
        case 'detector.update':
          setDetectorUpdate(msg);
          break;
      }
    };
    addSubscriber(cb);
    return () => removeSubscriber(cb);
  }, [addSubscriber, removeSubscriber]);

  return {
    connected,
    systemUpdate,
    alertUpdate,
    threatUpdate,
    detectorUpdate,
  };
}
