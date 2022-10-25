<script>
	import '../app.css';
	import { page } from '$app/stores';

	const routes = [
		{ href: '/', name: 'Home' },
		{ href: '/about', name: 'About' },
		{ href: '/data', name: 'Data selection' }
	];
</script>

<svelte:head>
	<title>Aud-it</title>
</svelte:head>

<div class="flex flex-col h-screen w-screen">
	<!-- <header>
		<div class="navbar bg-neutral text-neutral-content">
			<div class="navbar-start">
				<div class="dropdown">
					<label tabindex="0" class="btn btn-ghost btn-circle">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							><path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 6h16M4 12h16M4 18h7"
							/></svg
						>
					</label>
					<ul
						tabindex="0"
						class="menu menu-compact dropdown-content mt-3 p-2 shadow bg-base-100 rounded-box w-52"
					>
						{#each routes as route}
							<li>
								<a
									href={route.href}
									class="font-bold"
									class:text-blue-800={route.href !== $page.url.pathname}
									class:text-gray-800={route.href === $page.url.pathname}
									>{route.name}
								</a>
							</li>
						{/each}
					</ul>
				</div>
			</div>
			<div class="navbar-center">
				<a href="/" class="btn btn-ghost normal-case text-xl">AUD-it</a>
			</div>
			<div class="navbar-end">
				<a class="btn btn-ghost normal-case text-xl">?</a>
			</div>
		</div>
	</header> -->
	<slot />
</div>
