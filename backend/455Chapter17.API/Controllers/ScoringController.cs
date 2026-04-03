using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using _455chapter17.API.Data;
using _455chapter17.API.Models;

namespace _455chapter17.API.Controllers;

[ApiController]
[Route("api/scoring")]
public class ScoringController(AppDbContext db) : ControllerBase
{
    [HttpPost("run")]
    public async Task<IActionResult> RunScoring()
    {
        var orders = await db.Orders.ToListAsync();
        var scoredAt = DateTime.UtcNow;

        foreach (var order in orders)
        {
            var existing = await db.DeliveryScores.FindAsync(order.OrderId);
            var probability = Math.Round(order.RiskScore / 100m, 4);

            if (existing is null)
            {
                db.DeliveryScores.Add(new DeliveryScore
                {
                    OrderId = order.OrderId,
                    LateDeliveryProbability = probability,
                    ScoredAt = scoredAt,
                    ScoreSource = "risk_score",
                    ModelVersion = "v1.0"
                });
            }
            else
            {
                existing.LateDeliveryProbability = probability;
                existing.ScoredAt = scoredAt;
            }
        }

        await db.SaveChangesAsync();

        return Ok(new { message = "Scoring complete.", scored = orders.Count });
    }

    [HttpGet("queue")]
    public async Task<IActionResult> GetQueue()
    {
        var queue = await db.DeliveryScores
            .Include(ds => ds.Order)
            .ThenInclude(o => o!.Customer)
            .OrderByDescending(ds => ds.LateDeliveryProbability)
            .Take(100)
            .Select(ds => new
            {
                OrderId = ds.OrderId,
                CustomerName = ds.Order != null && ds.Order.Customer != null
                    ? ds.Order.Customer.FullName : "",
                OrderTotal = ds.Order != null ? ds.Order.OrderTotal : 0,
                RiskScore = ds.Order != null ? ds.Order.RiskScore : 0,
                FraudProbability = ds.LateDeliveryProbability,
                ScoredAt = ds.ScoredAt
            })
            .ToListAsync();

        return Ok(queue);
    }
}
