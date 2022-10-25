<script>
	import { group } from 'd3';
	export let selectedsets;
	export let groups;
	export let usermode;

	let entries;
	let values;

	$: if (groups) {
		entries = Object.entries(groups);
		values = Object.values(groups);
	}
</script>

<!-- dropdown to select group or user (ordered by group) -->
<div>
	<select bind:value={selectedsets} class="select w-full max-w-xs" required>
		{#if usermode == 'true'}
			<option value="" disabled selected>Select a user</option>
			{#if groups}
				{#each entries as [key, value]}
					<optgroup label={key}>
						{#each value as val}
							<option value={val}>{val}</option>
						{/each}
					</optgroup>
				{/each}
			{:else}
				<option value="">Loading users..</option>
			{/if}
		{:else}
			<option value="" disabled selected>Select a group</option>
			{#if groups}
				{#each entries as [key, value]}
					<option {value}>{key}</option>
				{/each}
			{:else}
				<option value="">Loading groups..</option>
			{/if}
		{/if}
	</select>
</div>
