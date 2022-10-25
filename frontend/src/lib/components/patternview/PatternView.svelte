<script>
	import BoopAction from '../boop/BoopAction.svelte';
	import HelpButton from '../boop/HelpButton.svelte';
	import { Circle3 } from 'svelte-loading-spinners';
	import { scale } from 'svelte/transition';
	import SummaryPlot from './SummaryPlot.svelte';
	import PatternPlot from './PatternPlot.svelte';
	import PatternSelection from './PatternSelection.svelte';
	export let selectedsets;
	export let selecteddurs;
	export let selectedhours;
	export let colorScale;
	export let intervalnames;
	export let highlight;
	export let reload;

	// Initiate parameters
	let summary_data;
	let reloadPlot = 0;
	let pattern_data;
	let updatePatterns = 0;
	let pattern_intervals;
	let pattern_relations;
	let patternloading = false;
	let summaryloading = false;

	// If component is reloaded, reset the parameters
	function startUpDur(reload) {
		summary_data = '';
		pattern_data = '';
		updatePatterns = '';
		reloadPlot = 0;
		pattern_intervals = '';
		pattern_relations = '';
		patternloading = false;
		summaryloading = false;
	}
	$: startUpDur(reload);

	// Load data for temporal summary
	async function loadSummary() {
		summary_data = '';
		summaryloading = true;
		let interval_names = JSON.stringify(intervalnames.map((d) => d.replaceAll('/', '-')));
		let selected_durs = JSON.stringify(selecteddurs);
		let _total_data = await fetch(
			'http://127.0.0.1:5000/get_summary_data/' +
				selectedsets +
				'/' +
				interval_names +
				'/' +
				selected_durs +
				'/' +
				selectedhours
		);
		summary_data = await _total_data.json();
		reloadPlot += 1;
	}

	// Load the intervals that need to be highlighted according to the selected pattern
	async function loadHighlight() {
		let interval_names = JSON.stringify(intervalnames.map((d) => d.replaceAll('/', '-')));
		let selected_durs = JSON.stringify(selecteddurs);
		let patternintervals = JSON.stringify(pattern_intervals.map((d) => d.replaceAll('/', '-')));
		let highlight_ = await fetch(
			'http://127.0.0.1:5000/highlight_patterns/' +
				selectedsets +
				'/' +
				interval_names +
				'/' +
				selected_durs +
				'/' +
				selectedhours +
				'/' +
				patternintervals +
				'/' +
				pattern_relations
		);
		highlight = await highlight_.json();
	}

	// If a new pattern is selected, reload the highlighted events
	$: if (pattern_intervals && pattern_relations) {
		loadHighlight();
	}
</script>

{#if summary_data}
	<div class="h-1/3 rounded border-2 border-slate-800 overflow-hidden">
		<div class="flex flex-row">
			<!-- Tooltip to explain the summary view -->
			<div
				class="tooltip tooltip-bottom z-10"
				data-tip="The summary view displays the average frequency and duration of selected intervals
				based on the selected duration- and time-range from the duration and the radial view."
			>
				<BoopAction boopParams={{ scale: 1.2, timing: 200 }}>
					<HelpButton />
				</BoopAction>
			</div>
			<div class="w-1/3" />
			<button class="mt-3 btn ghost-btn" on:click={loadSummary}>Show Temporal Summary</button>
		</div>
		<!-- Summary view -->
		<SummaryPlot bind:summary_data bind:colorScale bind:reloadPlot />
	</div>
{:else}
	<div class="h-1/3 rounded border-2 bg-slate-100 border-slate-800">
		<!-- Show empty component if data is not yet loaded -->
		{#if intervalnames.length > 0}
			<button class="mt-3 btn ghost-btn" on:click={loadSummary}>Show Temporal Summary</button>
			{#if summaryloading}
				<div class="flex justify-center items-center h-60">
					<Circle3 size="150" />
				</div>
			{:else}
				<div class="flex justify-center items-center h-80">
					<p
						class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
						data-tip="The summary view displays the average frequency and duration of selected intervals based on the selected duration- and time-range from the duration and the radial view."
					>
						Summary view
					</p>
				</div>
			{/if}
		{:else}
			<button class="mt-3 btn ghost-btn btn-disabled" on:click={loadSummary}
				>Show Temporal Summary</button
			>
			<div class="flex justify-center items-center h-80">
				<p
					class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
					data-tip="The summary view displays the average frequency and duration of selected intervals based on the selected duration- and time-range from the duration and the radial view."
				>
					Summary view
				</p>
			</div>
		{/if}
	</div>
{/if}
{#if summary_data}
	<div class="h-2/3 rounded border-2 border-slate-800 overflow-auto">
		<div class="flex flex-row">
			<!-- tooltip that explains the pattern view -->
			<div
				class="tooltip tooltip-right"
				data-tip="The pattern view can be used to mine patterns from the selected intervals in the time-range of interest. You can specify if the original sequence set should contain a specific interval. The resulting patterns are visualized according to the VERTIRP algorithm. By clicking on a pattern, the corresponding intervals will be highlighted in the radial view and can be further explored by pressing the 'show pattern sequences' button."
			>
				<BoopAction boopParams={{ scale: 1.2, timing: 200 }}>
					<HelpButton />
				</BoopAction>
			</div>
			<div class="w-1/4" />
			<div class="grid place-items-center">
				<!-- dropdown to indicate the sequences from which patterns should be mined -->
				<PatternSelection
					bind:intervalnames
					bind:selecteddurs
					bind:selectedhours
					bind:pattern_data
					bind:selectedsets
					bind:pattern_intervals
					bind:pattern_relations
					bind:patternloading
				/>
			</div>
		</div>
		{#if pattern_data}
			<div transition:scale>
				<!-- Pattern view -->
				<PatternPlot
					bind:pattern_data
					bind:colorScale
					bind:reloadPlot={updatePatterns}
					bind:pattern_intervals
					bind:pattern_relations
					bind:highlight
				/>
			</div>
		{:else if patternloading}
			<!-- Indicate data loaded -->
			<div class="flex justify-center items-center h-60">
				<Circle3 size="150" />
			</div>
		{:else}
			<!-- Show empty component if data is not loaded -->
			<div class="flex justify-center items-center h-80">
				<p
					class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
					data-tip="The pattern view can be used to mine patterns from the selected intervals in the time-range of interest. By clicking on a pattern, the corresponding intervals will be highlighted in the radial view and can be further explored."
				>
					Pattern view
				</p>
			</div>
		{/if}
	</div>
{:else}
	<!-- Show empty component if data is not loaded -->
	<div class="h-2/3 rounded border-2 bg-slate-100 border-slate-800">
		<div class="flex justify-center items-center h-80">
			<p
				class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
				data-tip="The pattern view can be used to mine patterns from the selected intervals in the time-range of interest. By clicking on a pattern, the corresponding intervals will be highlighted in the radial view and can be further explored."
			>
				Pattern view
			</p>
		</div>
	</div>
{/if}

<style>
	.tooltip {
		position: absolute;
	}
</style>
