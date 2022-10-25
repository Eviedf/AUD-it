<script>
	import { scale } from 'svelte/transition';
	import SelectionPane from './SelectionPane.svelte';
	import Matrix from './Matrix.svelte';
	import HelpButton from '../boop/HelpButton.svelte';
	import BoopAction from '../boop/BoopAction.svelte';
	export let intervals;
	export let selectedevent;
	export let intervalnames;
	export let attribute_list;
	export let events;
	export let colorScale;

	// Removes an interval from the selection (when a user clicks on a coloured cell or removes the badge)
	function removeInterval(intervalname) {
		const index = intervalnames.indexOf(intervalname);
		intervalnames.splice(index, 1);
		intervalnames = intervalnames;
	}
	// This variable includes the selected intervals
	$: intervalnames = intervalnames;
</script>

<div class="item h-2/3 w-full rounded border-2 border-slate-800">
	<div class="h-1/4">
		<div class="flex flex-row-reverse">
			<div
				class="tooltip tooltip-bottom"
				data-tip="The matrix view displays all the possible intervals within each event-type. The bars in each cell encode the average duration and frequency. A light stroke indicates that the interval has not been observed in the dataset. Outliers can be recognized through empty cells with a dark stroke. Use this overview to select intervals of interest, by clicking on a cell."
			>
				<!-- Tooltip that provides information about the matrix view -->
				<BoopAction boopParams={{ scale: 1.2, timing: 200 }}>
					<HelpButton />
				</BoopAction>
			</div>
		</div>
		<div class="mt-3 h-1/2 overflow-auto">
			<!-- Badges that indicate the selected intervals -->
			{#each intervalnames as intervalname}
				<span
					class="badge badge-lg mr-1 mt-1"
					style="background-color: {colorScale(intervalname)};"
					transition:scale
				>
					<span class="text-lg"
						>{intervalname}
						<button type="button" on:click={removeInterval(intervalname)}>
							<span aria-hidden="true">&times;</span>
						</button></span
					>
				</span>
			{/each}
		</div>
		<div class="h-1/4 mt-10 ml-20">
			<!-- A dropdown from which a user can select an event type to inspect its matrix -->
			<SelectionPane {events} bind:selectedevent />
		</div>
	</div>
	<div class="h-3/4 w-full">
		<!-- The matrix view -->
		<Matrix
			bind:intervals
			bind:selectedevent
			bind:intervalnames
			bind:colorScale
			{attribute_list}
			{events}
		/>
	</div>
</div>

<style>
</style>
