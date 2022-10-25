<script>
	export let events;
	export let selectedevent;
</script>

<!-- Dropdown to select event type of interest -->
<div>
	{#if events}
		<select bind:value={selectedevent}>
			{#each events as val}
				<option value={val}>
					{val}
				</option>
			{/each}
		</select>
	{/if}
</div>

<style>
</style>
