import type { PropsWithChildren } from 'react';

export const AppFrame = ({ children }: PropsWithChildren) => {
  return <div className="app-frame">{children}</div>;
};
