import brownie
import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module", autouse=True)
def initial_setup(gauge_v5, mock_lp_token, alice):
    mock_lp_token.approve(gauge_v5, LP_AMOUNT, {"from": alice})
    gauge_v5.deposit(LP_AMOUNT, {"from": alice})


def test_set_rewards_with_deposit(alice, coin_reward, reward_contract, mock_lp_token, gauge_v5):
    gauge_v5.add_reward(
        coin_reward,
        reward_contract,
        {"from": alice},
    )

    assert gauge_v5.reward_tokens(0) == coin_reward
    assert gauge_v5.reward_tokens(1) == ZERO_ADDRESS


def test_set_rewards_no_deposit(alice, coin_reward, reward_contract, mock_lp_token, gauge_v5):
    gauge_v5.add_reward(
        coin_reward,
        reward_contract,
        {"from": alice},
    )

    assert mock_lp_token.balanceOf(gauge_v5) == LP_AMOUNT
    assert gauge_v5.reward_tokens(0) == coin_reward
    assert gauge_v5.reward_tokens(1) == ZERO_ADDRESS


def test_multiple_reward_tokens(alice, coin_reward, coin_a, coin_b, reward_contract, gauge_v5):
    reward_tokens = [coin_reward, coin_a, coin_b, ZERO_ADDRESS]

    for i in range(4):
            gauge_v5.add_reward(
                reward_tokens[i],
                reward_contract,
                {"from": alice},
            )

    assert reward_tokens == [gauge_v5.reward_tokens(i) for i in range(4)]
