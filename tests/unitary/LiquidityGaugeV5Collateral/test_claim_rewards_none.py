from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(alice, bob, chain, gauge_v5_collateral, mock_lp_token, reward_contract, coin_reward):
    # Fund
    mock_lp_token.approve(gauge_v5_collateral, LP_AMOUNT, {"from": alice})
    gauge_v5_collateral.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(reward_contract, REWARD)
    reward_contract.notifyRewardAmount(REWARD, {"from": alice})

    gauge_v5_collateral.add_reward(
        coin_reward,
        reward_contract,
        {"from": alice},
    )

    chain.sleep(WEEK)

    gauge_v5_collateral.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(alice, bob, chain, gauge_v5_collateral, mock_lp_token, reward_contract, coin_reward):
    # Deposit
    mock_lp_token.transfer(bob, LP_AMOUNT, {"from": alice})
    mock_lp_token.approve(gauge_v5_collateral, LP_AMOUNT, {"from": bob})
    gauge_v5_collateral.deposit(LP_AMOUNT, {"from": bob})

    chain.sleep(WEEK)

    gauge_v5_collateral.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v5_collateral.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0
