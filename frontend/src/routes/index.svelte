<script>
	import { Circle3 } from 'svelte-loading-spinners';
	import DurationView from './../lib/components/durationview/durationView.svelte';
	import PatternView from '../lib/components/patternview/PatternView.svelte';
	import SelectionView from '../lib/components/selectionview/SelectionView.svelte';
	import MatrixView from '../lib/components/matrixview/MatrixView.svelte';
	import { onMount } from 'svelte';

	let groups;
	let reload = 0;
	let intervals;
	let selectedhours;
	let selectedsets;
	let timedata;
	let matrixloading = false;

	let events;
	// This is the event that is selected by default, change this for a different dataset
	let selectedevent = 'connectivity';
	let attribute_list;
	let selecteddurs = {};
	let intervalnames = new Array();
	let colorScale;
	let highlight;

	// Load the group dictionary
	async function loadgroups() {
		let _groups = await fetch('http://127.0.0.1:5000/get_groups');
		groups = await _groups.json();
	}

	// Load the events and their possible values/attributes
	async function loadevents() {
		let _events = await fetch('http://127.0.0.1:5000/get_events_attributes');
		let events_attr = await _events.json();
		events = events_attr[0];
		attribute_list = events_attr[1];
	}

	// Load groups and events when application starts
	onMount(() => {
		loadgroups();
		loadevents();
	});

	// When page reloads, reset these variables
	$: if (reload) {
		selecteddurs = {};
		intervalnames = new Array();
		timedata = '';
	}
</script>

<div class="flex h-screen">
	<div class="flex-row item w-1/3 h-screen text-center">
		<div class="bg-slate-800 h-1/3 rounded-lg border-2 border-black z-0">
			<div class="flex flex-row">
				<p class="ml-6 text-5xl mt-6 font-semibold text-white">AUD-it</p>
				<div class="item w-1/6" />
				<p class="text-2xl mt-6 font-semibold text-white">Data Selection</p>
			</div>
			<!-- Upper leftmost view, selection view in which a user can select a group or user of interest -->
			<SelectionView {groups} bind:intervals bind:selectedsets bind:reload bind:matrixloading />
		</div>
		{#if intervals}
			<!-- lower leftmost view, the matrix view -->
			<MatrixView
				bind:intervals
				bind:selectedevent
				bind:intervalnames
				bind:colorScale
				{attribute_list}
				{events}
			/>
		{:else}
			<!-- If there is no data loaded yet, display a box with matrix view information -->
			<div class="h-2/3 rounded bg-slate-100 border-2 border-slate-800">
				<div class="flex justify-center items-center h-80">
					<p
						class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
						data-tip="The matrix view displays all the possible intervals within each event-type. The bars in each cell encode the average duration and frequency from all intervals respectively. One can hover over the cells to analyse the exact values. If no tooltip appears, the interval has not been observed in this dataset."
					>
						Matrix view
					</p>
				</div>
				{#if matrixloading}
					<!-- Indicate that the matrix view is loading -->
					<div class="flex justify-center items-center h-60">
						<Circle3 size="150" />
					</div>
					<p>Loading... this might take a few minutes</p>
				{/if}
			</div>
		{/if}
	</div>
	<div class="flex-row item w-1/3 h-screen text-center">
		<!-- Middle component, duration view and radial view-->
		<DurationView
			bind:selecteddurs
			bind:selectedhours
			bind:colorScale
			bind:highlight
			bind:timedata
			bind:intervalnames
			bind:selectedsets
			bind:reload
		/>
	</div>
	<div class="flex-row item w-1/3 h-full text-center">
		<div class="flex flex-col h-full">
			<!-- Right component, temporal summary, and patter view -->
			<PatternView
				bind:selectedsets
				bind:intervalnames
				bind:selecteddurs
				bind:selectedhours
				bind:colorScale
				bind:highlight
				bind:reload
			/>
		</div>
	</div>
</div>

<style>
</style>
