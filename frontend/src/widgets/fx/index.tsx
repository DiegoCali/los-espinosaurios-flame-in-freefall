import type { Locale } from '@/shared/i18n';
import { SmoothScroll } from '@/shared/motion/smooth-scroll';
import { BootSequence } from './boot-sequence';
import { BOOT_KEY } from './boot-key';
import { EmberField } from './ember-field';
import { ScrollHud } from './scroll-hud';
import { CursorReticle } from './cursor-reticle';
import { RouteTransition } from './route-transition';
import { PageEnhancer } from './page-enhancer';
import './fx.css';

/** Inline head script: hides the boot overlay before first paint on repeat loads in a session. */
export const bootScript = `try{if(sessionStorage.getItem('${BOOT_KEY}')||matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.dataset.booted='1'}catch(e){document.documentElement.dataset.booted='1'}`;

export function GlobalFx({ locale }: { locale: Locale }) {
  return <>
    <SmoothScroll />
    <EmberField />
    <ScrollHud />
    <CursorReticle />
    <RouteTransition />
    <PageEnhancer />
    <BootSequence skip={locale === 'es' ? 'OMITIR' : 'SKIP'} />
  </>;
}
