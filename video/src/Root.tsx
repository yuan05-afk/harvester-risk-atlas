import React from 'react';
import { Composition } from 'remotion';
import { Film } from './Film';
import { DURATION, FPS, frames } from './timing';

export const Root: React.FC = () => <Composition id="Film" component={Film} durationInFrames={frames(DURATION)} fps={FPS} width={1920} height={1080} />;
