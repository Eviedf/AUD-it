<script>
	import Content from './modal/Content.svelte';
	import Modal from './modal/Modal.svelte';
	import { modal } from '../store/stores.js';
	export let timedata;
	export let highlight;
	export let colorScale;
	export let selectedhours;
</script>

<!-- Create detailed view popup (check PopupLong in modal, and timeline.svelte)-->
<Modal show={$modal}>
	<Content bind:timedata bind:highlight bind:colorScale bind:selectedhours />
</Modal>
