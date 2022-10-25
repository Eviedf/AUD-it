import { writable } from 'svelte/store';

// store to display popup
export const modal = writable( null );
export const windowStyle = writable( {} );