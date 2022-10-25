<script>
	import { getContext } from 'svelte';
	import PopupLong from './PopupLong.svelte';
	export let timedata;
	export let highlight;
	export let colorScale;
	export let selectedhours;

	const { open } = getContext('simple-modal');

	const showPopupLong = () => {
		open(PopupLong, {
			message: 'Detailed sequence analysis',
			timedata,
			highlight,
			colorScale,
			selectedhours
		});
	};
</script>

<section>
	{#if highlight}
		<button class="mt-3 btn ghost-btn" on:click={showPopupLong}>Show pattern sequences</button>
	{:else}
		<button class="mt-3 btn ghost-btn" on:click={showPopupLong}>Show raw sequences</button>
	{/if}
</section>

<style>
	section {
		padding-top: 0.5em;
	}
</style>
