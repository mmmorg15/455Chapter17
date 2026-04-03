using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using _455chapter17.API.Data;

namespace _455chapter17.API.Controllers;

[ApiController]
[Route("api/products")]
public class ProductsController(AppDbContext db) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var products = await db.Products
            .Where(p => p.IsActive)
            .Select(p => new
            {
                p.ProductId,
                p.Sku,
                p.ProductName,
                p.Category,
                p.Price,
                p.IsActive
            })
            .OrderBy(p => p.Category)
            .ThenBy(p => p.ProductName)
            .ToListAsync();

        return Ok(products);
    }
}
