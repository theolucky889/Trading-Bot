<template>
  <div class="flex flex-col items-center justify-center p-8 bg-gray-900 text-white min-h-screen">
    <h1 class="text-3xl font-bold mb-8">Login</h1>
    <p class="text-lg text-gray-300">Please enter your credentials.</p>
    <input type="email" placeholder="Email" class="mb-4 p-2 rounded" />
    <input type="password" placeholder="Password" class="mb-4 p-2 rounded" />
    <div class="flex space-x-4">
      <button class="btn-futuristic">Login</button>
      <RouterLink class="btn-futuristic" to="/register">Register</RouterLink>
    </div>
  </div>
</template>


