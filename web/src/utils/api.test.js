import test from 'node:test';
import assert from 'node:assert/strict';
import { buildRouteAlternativesUrl } from './api.js';

test('buildRouteAlternativesUrl uses the selected src and dst values', () => {
  assert.equal(buildRouteAlternativesUrl(101, 127), '/route/alternatives?src=101&dst=127');
});

test('buildRouteAlternativesUrl falls back to the corridor defaults', () => {
  assert.equal(buildRouteAlternativesUrl(undefined, undefined), '/route/alternatives?src=101&dst=127');
});
