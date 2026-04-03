using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace _455chapter17.API.Models;

[Table("products")]
public class Product
{
    [Key]
    [Column("product_id")]
    public int ProductId { get; set; }

    [Column("sku")]
    public string Sku { get; set; } = "";

    [Column("product_name")]
    public string ProductName { get; set; } = "";

    [Column("category")]
    public string Category { get; set; } = "";

    [Column("price")]
    public decimal Price { get; set; }

    [Column("cost")]
    public decimal Cost { get; set; }

    [Column("is_active")]
    public bool IsActive { get; set; }
}
