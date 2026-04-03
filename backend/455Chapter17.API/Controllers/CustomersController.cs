using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using _455chapter17.API.Data;

namespace _455chapter17.API.Controllers;

[ApiController]
[Route("api/customers")]
public class CustomersController(AppDbContext db) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var customers = await db.Customers
            .Where(c => c.IsActive)
            .Select(c => new
            {
                c.CustomerId,
                c.FullName,
                c.Email,
                c.City,
                c.State,
                c.CustomerSegment,
                c.LoyaltyTier,
                c.IsActive
            })
            .OrderBy(c => c.FullName)
            .ToListAsync();

        return Ok(customers);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var customer = await db.Customers
            .Where(c => c.CustomerId == id)
            .Select(c => new
            {
                c.CustomerId,
                c.FullName,
                c.Email,
                c.City,
                c.State,
                c.CustomerSegment,
                c.LoyaltyTier,
                c.IsActive
            })
            .FirstOrDefaultAsync();

        if (customer is null) return NotFound();
        return Ok(customer);
    }
}
