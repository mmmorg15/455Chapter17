using Microsoft.EntityFrameworkCore;
using _455chapter17.API.Models;

namespace _455chapter17.API.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Customer> Customers => Set<Customer>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    public DbSet<DeliveryScore> DeliveryScores => Set<DeliveryScore>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Order>()
            .HasOne(o => o.Customer)
            .WithMany()
            .HasForeignKey(o => o.CustomerId);

        modelBuilder.Entity<Order>()
            .HasMany(o => o.OrderItems)
            .WithOne()
            .HasForeignKey(oi => oi.OrderId);

        modelBuilder.Entity<DeliveryScore>()
            .HasOne(ds => ds.Order)
            .WithOne()
            .HasForeignKey<DeliveryScore>(ds => ds.OrderId);
    }
}
