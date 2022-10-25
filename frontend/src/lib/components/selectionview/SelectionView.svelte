<script>
	// @ts-nocheck
	import UserDatePane from './UserDatePane.svelte';
	export let groups;
	export let intervals;
	export let selectedsets;
	export let reload;
	export let matrixloading;

	// if usermode = true, update dropdown to only include users, otherwise only show groups in dropdown
	let usermode = false;

	// Load matrix data
	async function loadMatrixData() {
		reload += 1;
		matrixloading = true;
		console.log('loading group data');
		intervals = '';
		let _patterns = await fetch('http://127.0.0.1:5000/get_attr_matrices/' + selectedsets);
		intervals = await _patterns.json();
	}
</script>

<div class="flex-column justify-center grow-0">
	<div>
		<!-- radio buttons to indicate if someone wants to select a group or a user -->
		<form on:submit|preventDefault={loadMatrixData}>
			<div class="flex flex-column">
				<div class="item mt-6 w-1/6" />
				<div class="item mt-6 w-1/4">
					<label class="label cursor-pointer">
						<span class="label-text text-white font-semibold">Group</span>
						<input
							type="radio"
							bind:group={usermode}
							name="usermode1"
							value="false"
							class="radio"
							checked
							style="border-color: white;"
						/>
					</label>
				</div>
				<div class="item mt-6 w-1/6" />
				<div class="item mt-6 w-1/4">
					<label class="label cursor-pointer">
						<span class="label-text text-white font-semibold">User</span>
						<input
							type="radio"
							bind:group={usermode}
							name="usermode1"
							value="true"
							class="radio"
							style="border-color: white;"
						/>
					</label>
				</div>
				<div class="item mt-6 w-1/6" />
			</div>
			<div class="mt-6 item w-auto h-1/4">
				<!-- dropdown to display groups or users -->
				<UserDatePane {groups} bind:selectedsets bind:usermode />
			</div>
			<div>
				<button class="mt-6 mb-6 btn" type="submit"> Submit </button>
			</div>
		</form>
	</div>
</div>
