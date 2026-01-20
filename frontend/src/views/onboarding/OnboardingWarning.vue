<script setup>
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
</script>

<template>
  <div class="c-warning">
    <h1>Waarschuwing</h1>
    <img src="/images/waarschuwing.png" alt="Waarschuwing" class="c-warning__img" />
    <p class="c-warning__text">Schakel het systeem altijd uit via de pagina Apparaten. Trek nooit de stekker uit het stopcontact, dit kan het systeem beschadigen.</p>
    <div class="c-warning__progress">
      <div class="c-warning__progess-blocks">
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="true" />
      </div>
      <buttons-primary url="/games" title="Begin met trainen" />
    </div>
  </div>
</template>

<style scoped>
.c-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3rem;
  margin-top: 3rem;

  .c-warning__text {
    text-align: center;
    padding: 0 1rem;
    max-width: 20rem;
  }

  .c-warning__progess-blocks {
    display: flex;
    gap: 0.5rem;
  }

  .c-warning__progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    margin-top: 2rem;
    width: 100%;
    padding: 0rem 1.25rem;

    position: absolute;
    bottom: 2rem;
  }

  .c-warning__img {
    width: 90%;
    max-width: 20rem;
    height: auto;
  }
}
</style>
